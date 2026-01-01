"""
Chat WebSocket Consumer.

Handles real-time chat messaging, typing indicators, and read receipts.
"""
import asyncio
import json
import logging
from typing import Any, Dict, Optional, Tuple

import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from django.conf import settings

from .models import Message, Conversation
from profiles.models import Profile


logger = logging.getLogger('gymgem.websocket')

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL: int = 30


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat functionality.
    
    Features:
    - Real-time message sending/receiving
    - Typing indicators
    - Read receipts
    - Message editing and deletion
    - Heartbeat mechanism for connection health
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.conversation_id: Optional[int] = None
        self.room_group_name: Optional[str] = None
        self.profile: Optional[Profile] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    @sync_to_async
    def _get_profile_from_token(self, token: str) -> Optional[Profile]:
        """Extract profile from JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            profile_id = payload.get("current_profile")
            if not profile_id:
                return None
            return Profile.objects.get(id=profile_id)
        except (jwt.InvalidTokenError, Profile.DoesNotExist) as e:
            logger.warning("Token validation failed: %s", str(e))
            return None

    @sync_to_async
    def _edit_message_sync(
        self,
        message_id: int,
        profile_id: int,
        new_content: str
    ) -> Tuple[Optional[Message], Optional[str]]:
        """Edit a message synchronously."""
        try:
            msg = Message.objects.select_related("sender").get(id=message_id)
            if msg.sender_id != profile_id:
                return None, "You can only edit your own messages"
            if msg.is_deleted:
                return None, "Cannot edit a deleted message"
            cleaned = new_content.strip()
            if not cleaned:
                return None, "Content cannot be empty or whitespace only"
            msg.content = cleaned
            msg.edited_at = now()
            msg.save()
            return msg, None
        except Message.DoesNotExist:
            return None, "Message not found"

    @sync_to_async
    def _delete_message_sync(
        self,
        message_id: int,
        profile_id: int
    ) -> Tuple[Optional[Message], Optional[str]]:
        """Delete a message synchronously (soft delete)."""
        try:
            msg = Message.objects.select_related("sender").get(id=message_id)
            if msg.sender_id != profile_id:
                return None, "You can only delete your own messages"
            if msg.is_deleted:
                return None, "Message is already deleted"
            msg.is_deleted = True
            msg.content = ""
            msg.save()
            return msg, None
        except Message.DoesNotExist:
            return None, "Message not found"

    async def _send_heartbeat(self) -> None:
        """Send periodic heartbeat pings to keep connection alive."""
        while True:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                await self.send(json.dumps({
                    "type": "ping",
                    "timestamp": str(now())
                }))
                logger.debug(
                    "Heartbeat sent: conversation=%s, profile=%s",
                    self.conversation_id,
                    self.profile.id if self.profile else None
                )
            except Exception as e:
                logger.debug("Heartbeat stopped: %s", str(e))
                break

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        try:
            self.conversation_id = int(self.scope['url_route']['kwargs']['conversation_id'])
            self.room_group_name = f'chat_{self.conversation_id}'
            
            logger.info(
                "Chat WebSocket connection attempt for conversation %s",
                self.conversation_id
            )
            
            # Extract token from query string
            query_string = self.scope.get('query_string', b'').decode()
            token: Optional[str] = None
            if 'token=' in query_string:
                token = query_string.split('token=')[1].split('&')[0]
            
            # Reject if no token
            if not token:
                logger.warning(
                    "No token provided for conversation %s",
                    self.conversation_id
                )
                await self.close(code=4001)
                return
            
            # Get profile from token
            self.profile = await self._get_profile_from_token(token)
            if not self.profile:
                logger.warning(
                    "Authentication failed for conversation %s",
                    self.conversation_id
                )
                await self.close(code=4001)
                return
            
            # Check if conversation exists and profile is a participant
            try:
                conversation = await sync_to_async(Conversation.objects.get)(
                    id=self.conversation_id
                )
                is_participant = await sync_to_async(
                    lambda: conversation.participants.filter(id=self.profile.id).exists()
                )()
                
                if not is_participant:
                    logger.warning(
                        "Profile %s not authorized for conversation %s",
                        self.profile.id,
                        self.conversation_id
                    )
                    await self.close(code=4003)
                    return
                    
            except Conversation.DoesNotExist:
                logger.warning(
                    "Conversation %s not found",
                    self.conversation_id
                )
                await self.close(code=4004)
                return
            
            # Profile is authenticated and authorized - accept the connection
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            
            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(self._send_heartbeat())
            
            logger.info(
                "Chat WebSocket connected: conversation=%s, profile=%s",
                self.conversation_id,
                self.profile.id
            )
            
        except Exception as e:
            logger.error(
                "Unexpected error during connection: %s",
                str(e),
                exc_info=True
            )
            await self.close(code=4000)

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection."""
        # Cancel heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            
        # Remove channel from group when user disconnects
        if hasattr(self, 'room_group_name') and self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
        logger.info(
            "Chat WebSocket disconnected: conversation=%s, profile=%s, code=%s",
            self.conversation_id,
            self.profile.id if self.profile else None,
            close_code
        )

    async def receive(self, text_data: str) -> None:
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning(
                "Invalid JSON received in conversation %s",
                self.conversation_id
            )
            await self.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
            return
        
        try:
            message_type = data.get("type")
            
            # Handle PONG response (heartbeat acknowledgment)
            if message_type == "pong":
                logger.debug(
                    "Heartbeat PONG received: conversation=%s",
                    self.conversation_id
                )
                return
            
            # Handle read receipts
            if message_type == "read":
                await self.mark_message_read(data)
                return
            
            # Handle typing indicators
            if message_type == "typing":
                await self.handle_typing_indicator(data)
                return
            
            # Handle message editing
            if message_type == "edit":
                await self.handle_edit_message(data)
                return
            
            # Handle message deletion
            if message_type == "delete":
                await self.handle_delete_message(data)
                return
            
            # Otherwise, it's a regular chat message
            await self.handle_chat_message(data)
            
        except Conversation.DoesNotExist:
            logger.error(
                "Conversation %s not found during message handling",
                self.conversation_id
            )
            await self.send(json.dumps({
                "type": "error",
                "message": "Conversation not found"
            }))
        except Exception as e:
            logger.error(
                "Error handling message in conversation %s: %s",
                self.conversation_id,
                str(e),
                exc_info=True
            )
            await self.send(json.dumps({
                "type": "error",
                "message": "Failed to process message. Please try again."
            }))

    async def handle_chat_message(self, data: Dict[str, Any]) -> None:
        """Handle regular chat message."""
        message_content = data.get('content')
        
        # Validate content exists
        if not message_content:
            await self.send(json.dumps({
                "type": "error",
                "message": "Message content is required"
            }))
            return
        
        # Validate content is a string
        if not isinstance(message_content, str):
            await self.send(json.dumps({
                "type": "error",
                "message": "Message content must be a string"
            }))
            return
        
        # Validate content is not just whitespace
        if not message_content.strip():
            await self.send(json.dumps({
                "type": "error",
                "message": "Message content cannot be empty or whitespace only"
            }))
            return
        
        # Limit message length
        if len(message_content) > 5000:
            await self.send(json.dumps({
                "type": "error",
                "message": "Message content is too long (maximum 5000 characters)"
            }))
            return
        
        # Save message to database
        convo = await sync_to_async(Conversation.objects.get)(id=self.conversation_id)
        new_message = await sync_to_async(Message.objects.create)(
            conversation=convo, 
            sender=self.profile, 
            content=message_content.strip()
        )

        sender_name = await sync_to_async(
            lambda: self.profile.get_profile_data.name if self.profile else "anonymous"
        )()

        # Broadcast message to all participants
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message", 
                "message_id": new_message.id,
                "sender_id": self.profile.id,
                "sender_name": sender_name,
                "content": message_content.strip(),
                "timestamp": str(new_message.timestamp),
                "is_owner": True if self.profile.id == new_message.sender.id else False
            }
        )
        
        logger.debug(
            "Message sent in conversation %s by profile %s",
            self.conversation_id,
            self.profile.id
        )

    async def mark_message_read(self, data: Dict[str, Any]) -> None:
        """Mark a message as read and broadcast read receipt."""
        message_id = data.get("message_id")
        
        if not message_id:
            await self.send(json.dumps({
                "type": "error",
                "message": "message_id is required for read receipts"
            }))
            return
        
        try:
            message_id = int(message_id)
        except (ValueError, TypeError):
            await self.send(json.dumps({
                "type": "error",
                "message": "message_id must be a valid integer"
            }))
            return
        
        try:
            # Ensure the message exists and belongs to this conversation
            await sync_to_async(
                lambda: Message.objects.get(
                    id=message_id,
                    conversation_id=self.conversation_id
                )
            )()

            # Mark all messages in the conversation (except the reader's own) as read
            read_at_ts = now()
            await sync_to_async(
                lambda: Message.objects.filter(
                    conversation_id=self.conversation_id
                ).exclude(
                    sender_id=self.profile.id
                ).update(is_read=True, read_at=read_at_ts)
            )()

            reader_name = await sync_to_async(
                lambda: self.profile.get_profile_data.name if self.profile else "anonymous"
            )()
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "read_receipt",
                    "message_id": message_id,
                    "reader_id": self.profile.id,
                    "reader_name": reader_name,
                    "read_at": str(read_at_ts)
                }
            )
            
            logger.debug(
                "Messages marked as read in conversation %s by profile %s",
                self.conversation_id,
                self.profile.id
            )
            
        except Message.DoesNotExist:
            await self.send(json.dumps({
                "type": "error",
                "message": f"Message {message_id} not found in this conversation"
            }))

    async def handle_typing_indicator(self, data: Dict[str, Any]) -> None:
        """Handle typing indicator events."""
        try:
            is_typing = data.get("is_typing", False)
            
            if not isinstance(is_typing, bool):
                await self.send(json.dumps({
                    "type": "error",
                    "message": "is_typing must be a boolean value"
                }))
                return
            
            user_name = await sync_to_async(
                lambda: self.profile.get_profile_data.name if self.profile else "anonymous"
            )()
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "profile_id": self.profile.id,
                    "username": user_name,
                    "is_typing": is_typing
                }
            )
        except Exception as e:
            # Typing indicators are non-critical
            logger.debug("Typing indicator error: %s", str(e))

    async def handle_edit_message(self, data: Dict[str, Any]) -> None:
        """Handle message editing."""
        message_id = data.get("message_id")
        new_content = data.get("content") or data.get("new_content")
        
        if not message_id:
            await self.send(json.dumps({
                "type": "error",
                "message": "message_id is required for editing"
            }))
            return
        
        try:
            message_id = int(message_id)
        except (ValueError, TypeError):
            await self.send(json.dumps({
                "type": "error",
                "message": "message_id must be a valid integer"
            }))
            return
        
        if not new_content or not isinstance(new_content, str):
            await self.send(json.dumps({
                "type": "error",
                "message": "Valid 'content' or 'new_content' is required for editing"
            }))
            return
        
        if not new_content.strip():
            await self.send(json.dumps({
                "type": "error",
                "message": "Content cannot be empty or whitespace only"
            }))
            return
        
        if len(new_content) > 5000:
            await self.send(json.dumps({
                "type": "error",
                "message": "Content is too long (maximum 5000 characters)"
            }))
            return
        
        msg, error = await self._edit_message_sync(
            message_id,
            self.profile.id,
            new_content
        )
        
        if error:
            await self.send(json.dumps({
                "type": "error",
                "message": error
            }))
            return
        
        editor_name = await sync_to_async(
            lambda: self.profile.get_profile_data.name if self.profile else "anonymous"
        )()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "message_edited",
                "message_id": message_id,
                "content": msg.content,
                "edited_at": str(msg.edited_at),
                "editor_id": self.profile.id,
                "editor_name": editor_name,
                "sender_id": msg.sender_id,
                "timestamp": str(msg.timestamp),
                "is_deleted": msg.is_deleted,
            }
        )
        
        logger.info(
            "Message %s edited in conversation %s",
            message_id,
            self.conversation_id
        )

    async def handle_delete_message(self, data: Dict[str, Any]) -> None:
        """Handle message deletion (soft delete)."""
        message_id = data.get("message_id")
        
        if not message_id:
            await self.send(json.dumps({
                "type": "error",
                "message": "message_id is required for deletion"
            }))
            return
        
        try:
            message_id = int(message_id)
        except (ValueError, TypeError):
            await self.send(json.dumps({
                "type": "error",
                "message": "message_id must be a valid integer"
            }))
            return
        
        msg, error = await self._delete_message_sync(message_id, self.profile.id)
        
        if error:
            await self.send(json.dumps({
                "type": "error",
                "message": error
            }))
            return
        
        deleter_name = await sync_to_async(
            lambda: self.profile.get_profile_data.name if self.profile else "anonymous"
        )()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "message_deleted",
                "message_id": message_id,
                "deleter_id": self.profile.id,
                "deleter_name": deleter_name,
                "sender_id": msg.sender_id,
                "timestamp": str(msg.timestamp),
                "is_deleted": msg.is_deleted,
            }
        )
        
        logger.info(
            "Message %s deleted in conversation %s",
            message_id,
            self.conversation_id
        )

    async def read_receipt(self, event: Dict[str, Any]) -> None:
        """Send read receipt to WebSocket clients."""
        await self.send(json.dumps(event))

    async def typing_indicator(self, event: Dict[str, Any]) -> None:
        """Send typing indicator to WebSocket clients."""
        # Don't send typing indicator back to the person who is typing
        if event.get("profile_id") != self.profile.id:
            await self.send(json.dumps({
                "type": "typing",
                "profile_id": event.get("profile_id"),
                "username": event.get("username"),
                "is_typing": event.get("is_typing")
            }))

    async def chat_message(self, event: Dict[str, Any]) -> None:
        """Send chat message to WebSocket clients."""
        await self.send(json.dumps(event))

    async def message_edited(self, event: Dict[str, Any]) -> None:
        """Send message edit notification to WebSocket clients."""
        await self.send(json.dumps({
            "type": "edit",
            "message_id": event.get("message_id"),
            "content": event.get("content"),
            "edited_at": event.get("edited_at"),
            "editor_id": event.get("editor_id"),
            "editor_name": event.get("editor_name"),
            "sender_id": event.get("sender_id"),
            "timestamp": event.get("timestamp"),
            "is_deleted": event.get("is_deleted", False),
        }))

    async def message_deleted(self, event: Dict[str, Any]) -> None:
        """Send message deletion notification to WebSocket clients."""
        await self.send(json.dumps({
            "type": "delete",
            "message_id": event.get("message_id"),
            "deleter_id": event.get("deleter_id"),
            "deleter_name": event.get("deleter_name"),
            "sender_id": event.get("sender_id"),
            "timestamp": event.get("timestamp"),
            "is_deleted": event.get("is_deleted", True),
        }))
