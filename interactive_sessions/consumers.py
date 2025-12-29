import time
import jwt
import redis
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from profiles.models import Profile
from GymGem import settings
from .models import InteractiveSession


# Redis client (adjust host if needed)
redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)


def rkey(session_id, name):
    return f"session:{session_id}:{name}"


class InteractiveSessionConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket Consumer for Live 1-on-1 Interactive Sessions
    """
    
    # -----------------------------
    # Connection lifecycle
    # -----------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = None  # 'trainer' or 'trainee'
        self.group_name = None
        self.profile = None
        
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        # Extract token from query string (align with chat app behavior)
        query_string = self.scope.get("query_string", b"").decode()
        token = None
        if "token=" in query_string:
            token = query_string.split("token=")[1].split("&")[0]

        if not token:
            await self.close(code=4001)
            return

        self.profile = await self._get_profile_from_token(token)
        if not self.profile:
            await self.close(code=4001)
            return

        # Fetch the session and validate membership
        try:
            self.session = await self.get_session(self.session_id)
        except Exception as e:
            await self.close(code=4004)
            return

        # Fix: compare profile.id to trainer.id and trainee.id
        trainer_id = self.session.trainer.id if self.session.trainer else None
        trainee_id = self.session.trainee.id if self.session.trainee else None
        if self.profile.id not in (trainer_id, trainee_id):
            await self.close(code=4003)
            return

        # Fix: compare profile.id to trainer.id and trainee.id for role assignment
        self.role = (
            "trainer" if self.profile.id == trainer_id else "trainee"
        )

        self.group_name = f"session_{self.session_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # --- Disconnect after 40 minutes from slot start ---
        # Get slot_start_time from scheduled_at (TrainerCalendarSlot)
        slot_start_time = None
        try:
            slot_start_time = self.session.scheduled_at.slot_start_time
        except Exception:
            pass
        if slot_start_time:
            # Schedule a background task to check and disconnect after 40 minutes
            self.disconnect_task = self.scope["loop"].create_task(self._disconnect_after_40_minutes(slot_start_time))

    async def _disconnect_after_40_minutes(self, slot_start_time):
        """
        Disconnects the websocket if current time >= slot_start_time + 40 minutes
        """
        import asyncio
        now = timezone.now()
        target_time = slot_start_time + timezone.timedelta(minutes=40)
        seconds_to_wait = (target_time - now).total_seconds()
        if seconds_to_wait > 0:
            try:
                await asyncio.sleep(seconds_to_wait)
            except asyncio.CancelledError:
                return
        # If still connected, disconnect
        await self.close(code=4400)

    async def disconnect(self, close_code):
        await self.handle_leave()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        event_type = content.get("type")

        if event_type == "JOIN_SESSION":
            print(f"[JOIN_SESSION] {self.role} (Profile ID: {self.profile.id}) joining session {self.session_id}")
            await self.handle_join()

        elif event_type == "LEAVE_SESSION":
            print(f"[LEAVE_SESSION] {self.role} (Profile ID: {self.profile.id}) leaving session {self.session_id}")
            await self.handle_leave()

        # ---------- WebRTC signaling (pass-through) ----------
        elif event_type in ("OFFER", "ANSWER", "ICE_CANDIDATE"):
            payload_size = len(str(content))
            print(f"[WebRTC-IN] {self.role} (Profile ID: {self.profile.id}) sent {event_type}, payload size: {payload_size} bytes, session: {self.session_id}")
            if event_type in ("OFFER", "ANSWER"):
                sdp_type = content.get("sdp", {}).get("type", "unknown")
                print(f"[WebRTC-SDP] {event_type} sdp.type={sdp_type}")
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "signal.message",
                    "payload": content,
                    "from": self.role,
                },
            )
            print(f"[WebRTC-BROADCAST] {event_type} from {self.role} sent to group {self.group_name}")

    # -----------------------------
    # Group events
    # -----------------------------
    async def signal_message(self, event):
        # Do not echo back to sender
        msg_type = event["payload"].get("type", "unknown")
        from_role = event.get("from", "unknown")
        
        if event.get("from") == self.role:
            print(f"[WebRTC-FILTER] Skipping {msg_type} echo to sender {self.role} (Profile ID: {self.profile.id})")
            return
        
        print(f"[WebRTC-OUT] Forwarding {msg_type} from {from_role} to {self.role} (Profile ID: {self.profile.id}), session: {self.session_id}")
        await self.send_json(event["payload"])
        print(f"[WebRTC-SENT] {msg_type} successfully sent to {self.role} (Profile ID: {self.profile.id})")

    async def emit(self, payload):
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "broadcast", "payload": payload},
        )

    async def broadcast(self, event):
        await self.send_json(event["payload"])

    # -----------------------------
    # Session logic
    # -----------------------------
    async def handle_join(self):
        now_ts = int(time.time())
        redis_client.set(rkey(self.session_id, f"{self.role}_online"), 1)
        print(f"[Presence] {self.role} (Profile ID: {self.profile.id}) marked online in Redis for session {self.session_id}")
        
        # Check who else is online
        trainer_online = redis_client.get(rkey(self.session_id, "trainer_online"))
        trainee_online = redis_client.get(rkey(self.session_id, "trainee_online"))
        print(f"[Presence] Session {self.session_id} presence: trainer_online={trainer_online}, trainee_online={trainee_online}")
        
        await self.emit({"type": "USER_JOINED", "role": self.role, "timestamp": now_ts})
        print(f"[Broadcast] USER_JOINED event sent for {self.role} (Profile ID: {self.profile.id})")

        # Trainer enters -> session starts (waiting)
        if self.role == "trainer" and self.session.started_at is None:
            await self.start_session_waiting()

        # If both online -> LIVE
        if self.both_online():
            await self.go_live()

    async def handle_leave(self):
        redis_client.delete(rkey(self.session_id, f"{self.role}_online"))
        if self.session.status == "live":
            await self.stop_overlap()      
        if (self.role == "trainer" and self.session.status == "waiting"
            and not redis_client.get(rkey(self.session_id, "trainee_online")) and time.time() - self.session.started_at.timestamp() < 600):
            await self.noshow_abort()

    # -----------------------------
    # Helpers (Presence / Overlap)
    # -----------------------------
    def both_online(self):
        return (
            redis_client.get(rkey(self.session_id, "trainer_online"))
            and redis_client.get(rkey(self.session_id, "trainee_online"))
        )

    def half_completed(self):
        return bool(redis_client.get(rkey(self.session_id, "half_triggered")))

    async def start_overlap(self):
        if not redis_client.get(rkey(self.session_id, "overlap_started_at")):
            redis_client.set(rkey(self.session_id, "overlap_started_at"), int(time.time()))

    async def stop_overlap(self):
        started_at = redis_client.get(rkey(self.session_id, "overlap_started_at"))
        if started_at:
            started_at = int(started_at)
            total = int(redis_client.get(rkey(self.session_id, "total_overlap_seconds")) or 0)
            total += int(time.time()) - started_at
            redis_client.set(rkey(self.session_id, "total_overlap_seconds"), total)
            redis_client.delete(rkey(self.session_id, "overlap_started_at"))
            await self.check_half_completion(total)

    async def check_half_completion(self, total_overlap):
        required = 30
        if total_overlap >= required and not self.half_completed():
            redis_client.set(rkey(self.session_id, "half_triggered"), 1)
            await self.mark_completed()
            await self.emit({"type": "SESSION_HALF_COMPLETED"})

    # -----------------------------
    # State transitions (DB)
    # -----------------------------
    async def start_session_waiting(self):
        await self.update_session(
            status="waiting",
            started_at=timezone.now(),
        )
        await self.emit({"type": "SESSION_WAITING"})

    async def go_live(self):
        if self.session.status != "live":
            await self.update_session(status="live")
            await self.start_overlap()
            await self.emit({"type": "SESSION_LIVE"})

    async def mark_completed(self):
        await self.update_session(
            is_completed=True,
            status="completed",
            ended_at=timezone.now(),
        )


    async def abort_session(self, reason):
        await self.update_session(
            status="aborted",
            ended_at=timezone.now(),
        )
        await self.emit({"type": "SESSION_ABORTED", "reason": reason})
        
    async def noshow_abort(self):
        await self.update_session(status="no_show", ended_at=timezone.now())
        await self.emit({"type": "SESSION_NO_SHOW"})


    # -----------------------------
    # DB helpers
    # -----------------------------
    @sync_to_async
    def get_session(self, session_id):
        try:
            print("session_id",session_id)
            x= InteractiveSession.objects.select_related("scheduled_at", "trainer", "trainee").get(id=session_id)
            print("////////: ",x)
            return x
        except InteractiveSession.DoesNotExist:
            print("session not found")
            return None

    @sync_to_async
    def update_session(self, **fields):
        for k, v in fields.items():
            setattr(self.session, k, v)
        self.session.save(update_fields=list(fields.keys()))

    @sync_to_async
    def _get_profile_from_token(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            profile_id = payload.get("current_profile")
            if not profile_id:
                return None
            return Profile.objects.get(id=profile_id)
        except (jwt.InvalidTokenError, Profile.DoesNotExist):
            return None
