import jwt
import redis
import asyncio

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from profiles.models import Profile
from .models import InteractiveSession


# ================= Redis =================
redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

SESSION_TTL = 60 * 4
PRESENCE_TTL = SESSION_TTL + 60

MIN_PRESENCE_SECONDS = 1 * 60  # 5 minutes


def rkey(session_id, key):
    return f"session:{session_id}:{key}"


def ckey(session_id, role):
    return f"session:{session_id}:{role}_channel"


def now_ts():
    return timezone.now().timestamp()


# ================= Consumer =================
class InteractiveSessionConsumer(AsyncJsonWebsocketConsumer):
    """
    Production-grade WebRTC signaling + session finalization consumer.

    Final decision happens ONLY in force_disconnect().
    Financial operations are idempotent and atomic.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.force_closed = False
        self.role = None
        self.session = None
        self.profile = None

    # ---------------- CONNECT ----------------

    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]

        self.profile = await self.authenticate()
        if not self.profile:
            return await self.close(code=4001)

        self.session = await self.get_session(self.session_id)
        if not self.session:
            return await self.close(code=4004)

        self.role = self.resolve_role()
        if not self.role:
            return await self.close(code=4003)

        await self.accept()

        redis_client.set(ckey(self.session_id, self.role), self.channel_name, ex=SESSION_TTL)
        await self._presence_join(self.role)
        await self.schedule_auto_disconnect()

    async def schedule_auto_disconnect(self):
        started_at = self.session.started_at or timezone.now()
        if timezone.is_naive(started_at):
            started_at = timezone.make_aware(started_at)

        disconnect_time = started_at + timezone.timedelta(minutes=4)
        delay = (disconnect_time - timezone.now()).total_seconds()

        loop = asyncio.get_event_loop()
        if delay <= 0:
            loop.call_soon(lambda: asyncio.create_task(self.force_disconnect()))
        else:
            loop.call_later(delay, lambda: asyncio.create_task(self.force_disconnect()))

    # ---------------- FORCE CLOSE ----------------

    async def force_disconnect(self):
        if self.force_closed:
            return

        self.force_closed = True
        await self._presence_finalize_all()

        trainer_seconds = await self._get_presence_acc("trainer")
        trainee_seconds = await self._get_presence_acc("trainee")

        if trainer_seconds < MIN_PRESENCE_SECONDS:
            await self._mark_aborted("trainer_insufficient_time")
        elif trainee_seconds < MIN_PRESENCE_SECONDS:
            await self._mark_no_show()
        else:
            await self._mark_completed()

        await self.broadcast({"type": "SESSION_FINISHED"})
        self._cleanup_presence_keys()

        try:
            await self.close(code=4000)
        except Exception:
            pass

    # ---------------- DISCONNECT ----------------

    async def disconnect(self, close_code):
        redis_client.delete(ckey(self.session_id, self.role))
        if not self.force_closed:
            await self.handle_leave()

    # ---------------- RECEIVE ----------------

    async def receive_json(self, content):
        t = content.get("type")
        if t == "JOIN_SESSION":
            await self.handle_join()
        elif t == "LEAVE_SESSION":
            await self.handle_leave()
        elif t in ("OFFER", "ANSWER", "ICE_CANDIDATE"):
            await self.forward_webrtc(t, content)

    # ---------------- WEBRTC ----------------

    async def forward_webrtc(self, event_type, payload):
        if event_type == "OFFER" and self.role != "trainer":
            return
        if event_type == "ANSWER" and self.role != "trainee":
            return

        target_role = "trainer" if self.role == "trainee" else "trainee"
        channel = redis_client.get(ckey(self.session_id, target_role))
        if not channel:
            return

        await self.channel_layer.send(channel, {
            "type": "direct_webrtc",
            "payload": payload,
        })

    async def direct_webrtc(self, event):
        if not self.force_closed:
            try:
                await self.send_json(event["payload"])
            except Exception:
                # Socket may have closed; ignore
                pass

    async def direct_message(self, event):
        """
        Generic direct message handler used for control events (SESSION_* etc.).
        """
        try:
            await self.send_json(event.get("payload"))
        except Exception:
            # Socket closed or send failed; ignore
            pass

    # ---------------- PRESENCE ----------------

    async def handle_join(self):
        redis_client.set(rkey(self.session_id, f"{self.role}_online"), 1, ex=PRESENCE_TTL)
        redis_client.setnx(rkey(self.session_id, f"{self.role}_joined_at"), now_ts())
        redis_client.setnx(rkey(self.session_id, f"{self.role}_acc"), 0)

        await self.notify_other({"type": "USER_JOINED", "role": self.role})

        if self.role == "trainer" and self.session.status == "scheduled":
            await self.set_waiting()
        if self.both_online():
            await self.go_live()

    async def handle_leave(self):
        if self.force_closed:
            return
        await self._presence_leave(self.role)
        await self.notify_other({"type": "USER_LEFT", "role": self.role})

    def both_online(self):
        return all(
            redis_client.exists(rkey(self.session_id, f"{r}_online"))
            for r in ("trainer", "trainee")
        )

    # ---------------- PRESENCE HELPERS ----------------

    async def _presence_join(self, role):
        redis_client.set(rkey(self.session_id, f"{role}_online"), 1, ex=PRESENCE_TTL)
        redis_client.setnx(rkey(self.session_id, f"{role}_joined_at"), now_ts())
        redis_client.setnx(rkey(self.session_id, f"{role}_acc"), 0)

    async def _presence_leave(self, role):
        joined = redis_client.get(rkey(self.session_id, f"{role}_joined_at"))
        if joined:
            delta = max(0, now_ts() - float(joined))
            redis_client.incrbyfloat(rkey(self.session_id, f"{role}_acc"), delta)

        redis_client.delete(rkey(self.session_id, f"{role}_joined_at"))
        redis_client.delete(rkey(self.session_id, f"{role}_online"))

    async def _presence_finalize_all(self):
        for role in ("trainer", "trainee"):
            if redis_client.exists(rkey(self.session_id, f"{role}_online")):
                await self._presence_leave(role)

    async def _get_presence_acc(self, role):
        return float(redis_client.get(rkey(self.session_id, f"{role}_acc")) or 0)

    def _cleanup_presence_keys(self):
        for role in ("trainer", "trainee"):
            for s in ("online", "joined_at", "acc"):
                redis_client.delete(rkey(self.session_id, f"{role}_{s}"))

    # ---------------- SESSION STATES ----------------

    async def set_waiting(self):
        await self.update_session(status="waiting", started_at=timezone.now())
        await self.broadcast({"type": "SESSION_WAITING"})

    async def go_live(self):
        if self.session.status != "live":
            await self.update_session(status="live")
            await self.broadcast({"type": "SESSION_LIVE"})

    # ---------------- FINALIZATION ----------------

    @sync_to_async
    def _apply_financials(self, trainer_amount=0, trainee_refund=0):
        with transaction.atomic():
            session = InteractiveSession.objects.select_for_update().get(id=self.session_id)

            if getattr(session, "financials_applied", False):
                return

            session.financials_applied = True
            session.save(update_fields=["financials_applied"])

            if trainer_amount:
                trainer = session.trainer.get_profile_data
                trainer.balance += trainer_amount
                trainer.save(update_fields=["balance"])

            if trainee_refund:
                trainee = session.trainee.get_profile_data
                trainee.balance += trainee_refund
                trainee.save(update_fields=["balance"])

    async def _mark_completed(self):
        @sync_to_async
        def complete():
            with transaction.atomic():
                s = InteractiveSession.objects.select_for_update().get(id=self.session_id)
                if s.status == "completed":
                    return 0
                s.status = "completed"
                s.is_completed = True
                s.ended_at = timezone.now()
                s.save()
                return float(s.fees or 0) * 0.92

        trainer_cut = await complete()
        if trainer_cut:
            await self._apply_financials(trainer_amount=trainer_cut)

        await self.broadcast({"type": "SESSION_COMPLETED"})

    async def _mark_aborted(self, reason):
        @sync_to_async
        def abort():
            with transaction.atomic():
                s = InteractiveSession.objects.select_for_update().get(id=self.session_id)
                if s.status in ("completed", "aborted", "no_show"):
                    return 0
                s.status = "aborted"
                s.ended_at = timezone.now()
                s.save()
                return float(s.fees or 0)

        refund = await abort()
        if refund:
            await self._apply_financials(trainee_refund=refund)

        await self.broadcast({"type": "SESSION_ABORTED", "reason": reason})

    async def _mark_no_show(self):
        @sync_to_async
        def no_show():
            with transaction.atomic():
                s = InteractiveSession.objects.select_for_update().get(id=self.session_id)
                if s.status in ("completed", "aborted", "no_show"):
                    return (0, 0)
                s.status = "no_show"
                s.ended_at = timezone.now()
                s.save()
                f = float(s.fees or 0)
                return (f * 0.40, f * 0.40)

        trainer_gain, trainee_refund = await no_show()
        if trainer_gain or trainee_refund:
            await self._apply_financials(
                trainer_amount=trainer_gain,
                trainee_refund=trainee_refund,
            )

        await self.broadcast({
            "type": "SESSION_NO_SHOW",
            "trainer_gain": trainer_gain,
            "trainee_refund": trainee_refund,
        })

    # ---------------- AUTH ----------------

    async def authenticate(self):
        qs = self.scope.get("query_string", b"").decode()
        token = qs.split("token=")[1].split("&")[0] if "token=" in qs else None
        if not token:
            return None
        return await self.get_profile_from_token(token)

    def resolve_role(self):
        if self.profile.id == self.session.trainer_id:
            return "trainer"
        if self.profile.id == self.session.trainee_id:
            return "trainee"
        return None

    @sync_to_async
    def get_profile_from_token(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return Profile.objects.get(id=payload.get("current_profile"))
        except Exception:
            return None

    @sync_to_async
    def get_session(self, session_id):
        return InteractiveSession.objects.select_related("trainer", "trainee").get(id=session_id)

    @sync_to_async
    def update_session(self, **fields):
        for k, v in fields.items():
            setattr(self.session, k, v)
        self.session.save(update_fields=list(fields.keys()))

    async def broadcast(self, payload):
        for role in ("trainer", "trainee"):
            ch = redis_client.get(ckey(self.session_id, role))
            if ch:
                await self.channel_layer.send(ch, {
                    "type": "direct_message",
                    "payload": payload,
                })

    async def notify_other(self, payload):
        target_role = "trainer" if self.role == "trainee" else "trainee"
        target_channel = redis_client.get(ckey(self.session_id, target_role))
        if not target_channel:
            return
        await self.channel_layer.send(
            target_channel,
            {
                "type": "direct_message",
                "payload": payload,
            },
        )
