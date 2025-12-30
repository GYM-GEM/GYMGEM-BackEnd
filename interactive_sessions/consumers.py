import time
import jwt
import redis
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.conf import settings
from profiles.models import Profile
from .models import InteractiveSession

redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

SESSION_TTL = 60 * 60  # 1 hour


def rkey(session_id, key):
    return f"session:{session_id}:{key}"


class InteractiveSessionConsumer(AsyncJsonWebsocketConsumer):
    """
    Stable 1-to-1 WebRTC signaling consumer
    Trainer = Offerer only
    Trainee = Answer only
    """

    # -------------------- Connect --------------------

    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.profile = await self.authenticate()
        if not self.profile:
            await self.close(code=4001)
            return

        self.session = await self.get_session(self.session_id)
        if not self.session:
            await self.close(code=4004)
            return

        self.role = self.resolve_role()
        if not self.role:
            await self.close(code=4003)
            return

        self.group_name = f"session_{self.session_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    # -------------------- Disconnect --------------------

    async def disconnect(self, close_code):
        await self.handle_leave()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # -------------------- Receive --------------------

    async def receive_json(self, content):
        event = content.get("type")

        if event == "JOIN_SESSION":
            await self.handle_join()

        elif event == "LEAVE_SESSION":
            await self.handle_leave()

        elif event in ("OFFER", "ANSWER", "ICE_CANDIDATE"):
            await self.handle_webrtc(event, content)

    # -------------------- WebRTC --------------------

    async def handle_webrtc(self, event, payload):
        # Role enforcement
        if event == "OFFER" and self.role != "trainer":
            return
        if event == "ANSWER" and self.role != "trainee":
            return

        # Minimal validation
        if event in ("OFFER", "ANSWER") and "sdp" not in payload:
            return
        if event == "ICE_CANDIDATE" and "candidate" not in payload:
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "signal.forward",
                "payload": payload,
                "from": self.role,
            }
        )

    async def signal_forward(self, event):
        if event["from"] == self.role:
            return
        await self.send_json(event["payload"])

    # -------------------- Presence --------------------

    async def handle_join(self):
        redis_client.set(
            rkey(self.session_id, f"{self.role}_online"),
            1,
            ex=SESSION_TTL,
        )

        await self.broadcast({
            "type": "USER_JOINED",
            "role": self.role,
        })

        if self.role == "trainer" and self.session.status == "scheduled":
            await self.set_waiting()

        if self.both_online() and self.session.status != "live":
            await self.go_live()

    async def handle_leave(self):
        redis_client.delete(rkey(self.session_id, f"{self.role}_online"))

    def both_online(self):
        return (
            redis_client.exists(rkey(self.session_id, "trainer_online")) and
            redis_client.exists(rkey(self.session_id, "trainee_online"))
        )

    # -------------------- State --------------------

    async def set_waiting(self):
        await self.update_session(status="waiting", started_at=timezone.now())
        await self.broadcast({"type": "SESSION_WAITING"})

    async def go_live(self):
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
        await self.update_session(status="aborted", ended_at=timezone.now())
        await self.broadcast({"type": "SESSION_ABORTED", "reason": reason})

    # -------------------- Utils --------------------

    async def broadcast(self, payload):
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "broadcast", "payload": payload}
        )

    async def broadcast(self, event):
        await self.send_json(event["payload"])

    def resolve_role(self):
        if self.profile.id == self.session.trainer_id:
            return "trainer"
        if self.profile.id == self.session.trainee_id:
            return "trainee"
        return None

    # -------------------- Auth / DB --------------------

    async def authenticate(self):
        query = self.scope.get("query_string", b"").decode()
        token = None
        if "token=" in query:
            token = query.split("token=")[1].split("&")[0]
        if not token:
            return None
        return await self.get_profile_from_token(token)

    @sync_to_async
    def get_profile_from_token(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return Profile.objects.get(id=payload.get("current_profile"))
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
