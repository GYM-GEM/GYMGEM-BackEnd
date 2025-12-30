import jwt
import redis
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.conf import settings
from profiles.models import Profile
from .models import InteractiveSession


# ================= Redis =================
redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

SESSION_TTL = 60 * 60  # 1 hour


def rkey(session_id, key):
    return f"session:{session_id}:{key}"


def ckey(session_id, role):
    return f"session:{session_id}:{role}_channel"


# ================= Consumer =================
class InteractiveSessionConsumer(AsyncJsonWebsocketConsumer):
    """
    FINAL Stable 1-to-1 WebRTC signaling consumer

    trainer  -> OFFER
    trainee  -> ANSWER
    ICE      -> bidirectional
    """

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

        # 🔥 store channel name per role (CRITICAL)
        redis_client.set(
            ckey(self.session_id, self.role),
            self.channel_name,
            ex=SESSION_TTL,
        )

    # ---------------- DISCONNECT ----------------

    async def disconnect(self, close_code):
        redis_client.delete(ckey(self.session_id, self.role))
        await self.handle_leave()

    # ---------------- RECEIVE ----------------

    async def receive_json(self, content):
        event_type = content.get("type")

        if event_type == "JOIN_SESSION":
            await self.handle_join()

        elif event_type == "LEAVE_SESSION":
            await self.handle_leave()

        elif event_type in ("OFFER", "ANSWER", "ICE_CANDIDATE"):
            await self.forward_webrtc(event_type, content)

    # ---------------- WEBRTC (DIRECT) ----------------

    async def forward_webrtc(self, event_type, payload):
        """
        Forward WebRTC signaling DIRECTLY to the other peer
        """

        # ---- Role enforcement ----
        if event_type == "OFFER" and self.role != "trainer":
            return
        if event_type == "ANSWER" and self.role != "trainee":
            return

        # ---- Validation ----
        if event_type in ("OFFER", "ANSWER") and "sdp" not in payload:
            return
        if event_type == "ICE_CANDIDATE" and "candidate" not in payload:
            return

        target_role = "trainer" if self.role == "trainee" else "trainee"
        target_channel = redis_client.get(ckey(self.session_id, target_role))

        if not target_channel:
            return  # other peer not connected yet

        await self.channel_layer.send(
            target_channel,
            {
                "type": "direct.webrtc",
                "payload": payload,
            },
        )

    async def direct_webrtc(self, event):
        """
        Receive WebRTC signal sent directly to this socket
        """
        await self.send_json(event["payload"])

    # ---------------- PRESENCE ----------------

    async def handle_join(self):
        redis_client.set(
            rkey(self.session_id, f"{self.role}_online"),
            1,
            ex=SESSION_TTL,
        )

        # Notify the other peer ONLY
        await self.notify_other({
            "type": "USER_JOINED",
            "role": self.role,
        })

        # Session state
        if self.role == "trainer" and self.session.status == "scheduled":
            await self.set_waiting()

        if self.both_online():
            await self.go_live()

    async def handle_leave(self):
        redis_client.delete(rkey(self.session_id, f"{self.role}_online"))

    def both_online(self):
        return (
            redis_client.exists(rkey(self.session_id, "trainer_online"))
            and redis_client.exists(rkey(self.session_id, "trainee_online"))
        )

    async def notify_other(self, payload):
        target_role = "trainer" if self.role == "trainee" else "trainee"
        target_channel = redis_client.get(ckey(self.session_id, target_role))

        if not target_channel:
            return

        await self.channel_layer.send(
            target_channel,
            {
                "type": "direct.message",
                "payload": payload,
            },
        )

    async def direct_message(self, event):
        await self.send_json(event["payload"])

    # ---------------- SESSION STATE ----------------

    async def set_waiting(self):
        await self.update_session(
            status="waiting",
            started_at=timezone.now(),
        )
        await self.broadcast({"type": "SESSION_WAITING"})

    async def go_live(self):
        if self.session.status == "live":
            return
        await self.update_session(status="live")
        await self.broadcast({"type": "SESSION_LIVE"})

    async def mark_completed(self):
        await self.update_session(
            status="completed",
            ended_at=timezone.now(),
            is_completed=True,
        )
        await self.broadcast({"type": "SESSION_COMPLETED"})

    async def abort(self, reason):
        await self.update_session(
            status="aborted",
            ended_at=timezone.now(),
        )
        await self.broadcast({
            "type": "SESSION_ABORTED",
            "reason": reason,
        })

    # ---------------- BROADCAST (STATE ONLY) ----------------

    async def broadcast(self, payload):
        for role in ("trainer", "trainee"):
            channel = redis_client.get(ckey(self.session_id, role))
            if channel:
                await self.channel_layer.send(
                    channel,
                    {
                        "type": "direct.message",
                        "payload": payload,
                    },
                )

    # ---------------- AUTH / DB ----------------

    async def authenticate(self):
        query = self.scope.get("query_string", b"").decode()
        token = None

        if "token=" in query:
            token = query.split("token=")[1].split("&")[0]

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
            profile_id = payload.get("current_profile")
            return Profile.objects.get(id=profile_id)
        except Exception:
            return None

    @sync_to_async
    def get_session(self, session_id):
        try:
            return InteractiveSession.objects.select_related(
                "trainer", "trainee"
            ).get(id=session_id)
        except InteractiveSession.DoesNotExist:
            return None

    @sync_to_async
    def update_session(self, **fields):
        for k, v in fields.items():
            setattr(self.session, k, v)
        self.session.save(update_fields=list(fields.keys()))
