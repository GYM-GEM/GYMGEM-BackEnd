"""
Interactive Session WebSocket Consumer.

Handles WebRTC signaling and session management for 1:1 interactive sessions.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

import jwt
import redis

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from profiles.models import Profile
from .models import InteractiveSession


logger = logging.getLogger('gymgem.websocket')

# ================= Redis Configuration =================
# Use centralized Redis settings from Django settings


def get_redis_client() -> redis.Redis:
    """
    Get Redis client using centralized configuration from settings.
    """
    return redis.Redis(
        host=getattr(settings, 'REDIS_HOST', '127.0.0.1'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=getattr(settings, 'REDIS_DB', 0),
        password=getattr(settings, 'REDIS_PASSWORD', None),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


# Lazy initialization of Redis client
_redis_client: Optional[redis.Redis] = None


def redis_client() -> redis.Redis:
    """Get or create Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = get_redis_client()
    return _redis_client


SESSION_TTL: int = 60 * 4  # 40 minutes
PRESENCE_TTL: int = SESSION_TTL + 60
MIN_PRESENCE_SECONDS: int = 1 * 60  # 10 minutes
HEARTBEAT_INTERVAL: int = 30  # seconds


def rkey(session_id: int, key: str) -> str:
    """Generate Redis key for session data."""
    return f"session:{session_id}:{key}"


def ckey(session_id: int, role: str) -> str:
    """Generate Redis key for channel storage."""
    return f"session:{session_id}:{role}_channel"


def now_ts() -> float:
    """Get current timestamp."""
    return timezone.now().timestamp()


# ================= Consumer =================
class InteractiveSessionConsumer(AsyncJsonWebsocketConsumer):
    """
    Production-grade WebRTC signaling + session finalization consumer.

    Features:
    - WebRTC signaling (OFFER, ANSWER, ICE_CANDIDATE)
    - Presence tracking for trainer and trainee
    - Automatic session finalization after 40 minutes
    - Heartbeat mechanism for connection health
    - Financial operations (atomic and idempotent)
    
    Final decision happens ONLY in force_disconnect().
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.force_closed: bool = False
        self.role: Optional[str] = None
        self.session: Optional[InteractiveSession] = None
        self.profile: Optional[Profile] = None
        self.session_id: Optional[int] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    # ---------------- CONNECT ----------------

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        self.session_id = int(self.scope["url_route"]["kwargs"]["session_id"])
        
        logger.info(
            "WebSocket connection attempt for session %s",
            self.session_id
        )

        self.profile = await self.authenticate()
        if not self.profile:
            logger.warning(
                "Authentication failed for session %s",
                self.session_id
            )
            return await self.close(code=4001)

        self.session = await self.get_session(self.session_id)
        if not self.session:
            logger.warning(
                "Session %s not found",
                self.session_id
            )
            return await self.close(code=4004)

        self.role = self.resolve_role()
        if not self.role:
            logger.warning(
                "Profile %s not authorized for session %s",
                self.profile.id,
                self.session_id
            )
            return await self.close(code=4003)

        await self.accept()

        try:
            redis_client().set(
                ckey(self.session_id, self.role),
                self.channel_name,
                ex=SESSION_TTL
            )
        except redis.RedisError as e:
            logger.error("Redis error on connect: %s", str(e))
            return await self.close(code=4500)

        await self._presence_join(self.role)
        await self.schedule_auto_disconnect()
        
        # Start heartbeat
        self._heartbeat_task = asyncio.create_task(self._send_heartbeat())
        
        logger.info(
            "WebSocket connected: session=%s, role=%s, profile=%s",
            self.session_id,
            self.role,
            self.profile.id
        )

    async def _send_heartbeat(self) -> None:
        """Send periodic heartbeat pings to keep connection alive."""
        while not self.force_closed:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                if not self.force_closed:
                    await self.send_json({"type": "PING", "timestamp": now_ts()})
                    logger.debug(
                        "Heartbeat sent: session=%s, role=%s",
                        self.session_id,
                        self.role
                    )
            except Exception as e:
                logger.debug("Heartbeat stopped: %s", str(e))
                break

    async def schedule_auto_disconnect(self) -> None:
        """Schedule automatic disconnection after session time expires."""
        started_at = self.session.started_at or timezone.now()
        if timezone.is_naive(started_at):
            started_at = timezone.make_aware(started_at)

        disconnect_time = started_at + timezone.timedelta(minutes=40)
        delay = (disconnect_time - timezone.now()).total_seconds()

        loop = asyncio.get_event_loop()
        if delay <= 0:
            loop.call_soon(lambda: asyncio.create_task(self.force_disconnect()))
        else:
            loop.call_later(delay, lambda: asyncio.create_task(self.force_disconnect()))
            
        logger.info(
            "Auto-disconnect scheduled in %.0f seconds for session %s",
            max(0, delay),
            self.session_id
        )

    # ---------------- FORCE CLOSE ----------------

    async def force_disconnect(self) -> None:
        """Force disconnect and finalize session."""
        if self.force_closed:
            return

        self.force_closed = True
        
        # Cancel heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            
        logger.info("Force disconnecting session %s", self.session_id)
        
        await self._presence_finalize_all()

        trainer_seconds = await self._get_presence_acc("trainer")
        trainee_seconds = await self._get_presence_acc("trainee")

        logger.info(
            "Session %s presence: trainer=%.0fs, trainee=%.0fs",
            self.session_id,
            trainer_seconds,
            trainee_seconds
        )

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

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection."""
        # Cancel heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            
        if self.session_id and self.role:
            try:
                redis_client().delete(ckey(self.session_id, self.role))
            except redis.RedisError as e:
                logger.error("Redis error on disconnect: %s", str(e))
                
        if not self.force_closed:
            await self.handle_leave()
            
        logger.info(
            "WebSocket disconnected: session=%s, role=%s, code=%s",
            self.session_id,
            self.role,
            close_code
        )

    # ---------------- RECEIVE ----------------

    async def receive_json(self, content: Dict[str, Any]) -> None:
        """Handle incoming WebSocket messages."""
        t = content.get("type")
        
        # Handle PONG response (heartbeat acknowledgment)
        if t == "PONG":
            logger.debug("Heartbeat PONG received: session=%s", self.session_id)
            return
            
        if t == "JOIN_SESSION":
            await self.handle_join()
        elif t == "LEAVE_SESSION":
            await self.handle_leave()
        elif t in ("OFFER", "ANSWER", "ICE_CANDIDATE"):
            await self.forward_webrtc(t, content)
        else:
            logger.warning(
                "Unknown message type '%s' in session %s",
                t,
                self.session_id
            )

    # ---------------- WEBRTC ----------------

    async def forward_webrtc(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Forward WebRTC signaling messages to the other party."""
        if event_type == "OFFER" and self.role != "trainer":
            logger.warning("Non-trainer attempted to send OFFER")
            return
        if event_type == "ANSWER" and self.role != "trainee":
            logger.warning("Non-trainee attempted to send ANSWER")
            return

        target_role = "trainer" if self.role == "trainee" else "trainee"
        try:
            channel = redis_client().get(ckey(self.session_id, target_role))
        except redis.RedisError as e:
            logger.error("Redis error in forward_webrtc: %s", str(e))
            return
            
        if not channel:
            logger.debug(
                "Target %s not connected for session %s",
                target_role,
                self.session_id
            )
            return

        await self.channel_layer.send(channel, {
            "type": "direct_webrtc",
            "payload": payload,
        })

    async def direct_webrtc(self, event: Dict[str, Any]) -> None:
        """Handle direct WebRTC message from channel layer."""
        if not self.force_closed:
            try:
                await self.send_json(event["payload"])
            except Exception as e:
                logger.debug("Failed to send WebRTC message: %s", str(e))

    async def direct_message(self, event: Dict[str, Any]) -> None:
        """Generic direct message handler for control events."""
        try:
            await self.send_json(event.get("payload"))
        except Exception as e:
            logger.debug("Failed to send direct message: %s", str(e))

    # ---------------- PRESENCE ----------------

    async def handle_join(self) -> None:
        """Handle user joining the session."""
        try:
            client = redis_client()
            client.set(rkey(self.session_id, f"{self.role}_online"), 1, ex=PRESENCE_TTL)
            client.setnx(rkey(self.session_id, f"{self.role}_joined_at"), now_ts())
            client.setnx(rkey(self.session_id, f"{self.role}_acc"), 0)
        except redis.RedisError as e:
            logger.error("Redis error in handle_join: %s", str(e))

        await self.notify_other({"type": "USER_JOINED", "role": self.role})

        if self.role == "trainer" and self.session.status == "scheduled":
            await self.set_waiting()
        if self.both_online():
            await self.go_live()
            
        logger.info(
            "User joined: session=%s, role=%s",
            self.session_id,
            self.role
        )

    async def handle_leave(self) -> None:
        """Handle user leaving the session."""
        if self.force_closed:
            return
        await self._presence_leave(self.role)
        await self.notify_other({"type": "USER_LEFT", "role": self.role})
        
        logger.info(
            "User left: session=%s, role=%s",
            self.session_id,
            self.role
        )

    def both_online(self) -> bool:
        """Check if both trainer and trainee are online."""
        try:
            client = redis_client()
            return all(
                client.exists(rkey(self.session_id, f"{r}_online"))
                for r in ("trainer", "trainee")
            )
        except redis.RedisError as e:
            logger.error("Redis error in both_online: %s", str(e))
            return False

    # ---------------- PRESENCE HELPERS ----------------

    async def _presence_join(self, role: str) -> None:
        """Record presence join for a role."""
        try:
            client = redis_client()
            client.set(rkey(self.session_id, f"{role}_online"), 1, ex=PRESENCE_TTL)
            client.setnx(rkey(self.session_id, f"{role}_joined_at"), now_ts())
            client.setnx(rkey(self.session_id, f"{role}_acc"), 0)
        except redis.RedisError as e:
            logger.error("Redis error in _presence_join: %s", str(e))

    async def _presence_leave(self, role: str) -> None:
        """Record presence leave for a role and accumulate time."""
        try:
            client = redis_client()
            joined = client.get(rkey(self.session_id, f"{role}_joined_at"))
            if joined:
                delta = max(0, now_ts() - float(joined))
                client.incrbyfloat(rkey(self.session_id, f"{role}_acc"), delta)

            client.delete(rkey(self.session_id, f"{role}_joined_at"))
            client.delete(rkey(self.session_id, f"{role}_online"))
        except redis.RedisError as e:
            logger.error("Redis error in _presence_leave: %s", str(e))

    async def _presence_finalize_all(self) -> None:
        """Finalize presence for all roles."""
        for role in ("trainer", "trainee"):
            try:
                if redis_client().exists(rkey(self.session_id, f"{role}_online")):
                    await self._presence_leave(role)
            except redis.RedisError as e:
                logger.error("Redis error in _presence_finalize_all: %s", str(e))

    async def _get_presence_acc(self, role: str) -> float:
        """Get accumulated presence time for a role."""
        try:
            return float(redis_client().get(rkey(self.session_id, f"{role}_acc")) or 0)
        except redis.RedisError as e:
            logger.error("Redis error in _get_presence_acc: %s", str(e))
            return 0.0

    def _cleanup_presence_keys(self) -> None:
        """Clean up all presence-related Redis keys for this session."""
        try:
            client = redis_client()
            for role in ("trainer", "trainee"):
                for s in ("online", "joined_at", "acc"):
                    client.delete(rkey(self.session_id, f"{role}_{s}"))
        except redis.RedisError as e:
            logger.error("Redis error in _cleanup_presence_keys: %s", str(e))

    # ---------------- SESSION STATES ----------------

    async def set_waiting(self) -> None:
        """Set session to waiting state."""
        await self.update_session(status="waiting", started_at=timezone.now())
        await self.broadcast({"type": "SESSION_WAITING"})
        logger.info("Session %s set to waiting", self.session_id)

    async def go_live(self) -> None:
        """Set session to live state."""
        if self.session.status != "live":
            await self.update_session(status="live")
            await self.broadcast({"type": "SESSION_LIVE"})
            logger.info("Session %s is now live", self.session_id)

    # ---------------- FINALIZATION ----------------

    @sync_to_async
    def _apply_financials(
        self,
        trainer_amount: float = 0,
        trainee_refund: float = 0
    ) -> None:
        """Apply financial transactions atomically."""
        with transaction.atomic():
            session = InteractiveSession.objects.select_for_update().get(id=self.session_id)

            if getattr(session, "financials_applied", False):
                logger.info(
                    "Financials already applied for session %s",
                    self.session_id
                )
                return

            session.financials_applied = True
            session.save(update_fields=["financials_applied"])

            if trainer_amount:
                trainer = session.trainer.get_profile_data
                trainer.balance += trainer_amount
                trainer.save(update_fields=["balance"])
                logger.info(
                    "Trainer balance updated: session=%s, amount=%.2f",
                    self.session_id,
                    trainer_amount
                )

            if trainee_refund:
                trainee = session.trainee.get_profile_data
                trainee.balance += trainee_refund
                trainee.save(update_fields=["balance"])
                logger.info(
                    "Trainee refund applied: session=%s, amount=%.2f",
                    self.session_id,
                    trainee_refund
                )

    async def _mark_completed(self) -> None:
        """Mark session as completed."""
        @sync_to_async
        def complete() -> float:
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
        logger.info("Session %s marked as completed", self.session_id)

    async def _mark_aborted(self, reason: str) -> None:
        """Mark session as aborted."""
        @sync_to_async
        def abort() -> float:
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
        logger.info("Session %s aborted: %s", self.session_id, reason)

    async def _mark_no_show(self) -> None:
        """Mark session as no-show."""
        @sync_to_async
        def no_show() -> tuple:
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
        logger.info("Session %s marked as no-show", self.session_id)

    # ---------------- AUTH ----------------

    async def authenticate(self) -> Optional[Profile]:
        """Authenticate the WebSocket connection using JWT token."""
        qs = self.scope.get("query_string", b"").decode()
        token = qs.split("token=")[1].split("&")[0] if "token=" in qs else None
        if not token:
            return None
        return await self.get_profile_from_token(token)

    def resolve_role(self) -> Optional[str]:
        """Determine the role of the connected profile in this session."""
        if self.profile.id == self.session.trainer_id:
            return "trainer"
        if self.profile.id == self.session.trainee_id:
            return "trainee"
        return None

    @sync_to_async
    def get_profile_from_token(self, token: str) -> Optional[Profile]:
        """Extract profile from JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return Profile.objects.get(id=payload.get("current_profile"))
        except Exception as e:
            logger.warning("Token validation failed: %s", str(e))
            return None

    @sync_to_async
    def get_session(self, session_id: int) -> Optional[InteractiveSession]:
        """Get session by ID with related data."""
        try:
            return InteractiveSession.objects.select_related(
                "trainer", "trainee"
            ).get(id=session_id)
        except InteractiveSession.DoesNotExist:
            return None

    @sync_to_async
    def update_session(self, **fields: Any) -> None:
        """Update session fields."""
        for k, v in fields.items():
            setattr(self.session, k, v)
        self.session.save(update_fields=list(fields.keys()))

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        """Broadcast a message to both trainer and trainee."""
        for role in ("trainer", "trainee"):
            try:
                ch = redis_client().get(ckey(self.session_id, role))
                if ch:
                    await self.channel_layer.send(ch, {
                        "type": "direct_message",
                        "payload": payload,
                    })
            except redis.RedisError as e:
                logger.error("Redis error in broadcast: %s", str(e))

    async def notify_other(self, payload: Dict[str, Any]) -> None:
        """Notify the other party in the session."""
        target_role = "trainer" if self.role == "trainee" else "trainee"
        try:
            target_channel = redis_client().get(ckey(self.session_id, target_role))
            if not target_channel:
                return
            await self.channel_layer.send(
                target_channel,
                {
                    "type": "direct_message",
                    "payload": payload,
                },
            )
        except redis.RedisError as e:
            logger.error("Redis error in notify_other: %s", str(e))
