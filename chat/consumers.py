import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from .models import Message, Conversation
from profiles.models import Profile
from GymGem import settings

class ChatConsumer(AsyncWebsocketConsumer):
    @sync_to_async
    def _get_profile_from_token(self, token):
        """Extract profile from JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            profile_id = payload.get("current_profile")
            if not profile_id:
                return None
            return Profile.objects.get(id=profile_id)
        except (jwt.InvalidTokenError, Profile.DoesNotExist):
            return None

    @sync_to_async
    def _edit_message_sync(self, message_id, profile_id, new_content):
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

    @sync_to_async
    def _delete_message_sync(self, message_id, profile_id):
        msg = Message.objects.select_related("sender").get(id=message_id)
        if msg.sender_id != profile_id:
            return None, "You can only delete your own messages"
        if msg.is_deleted:
            return None, "Message is already deleted"
        msg.is_deleted = True
        msg.content = ""
        msg.save()
        return msg, None

    async def connect(self):
        try:
            self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
            self.room_group_name = f'chat_{self.conversation_id}'
            
            # Extract token from query string
            query_string = self.scope.get('query_string', b'').decode()
            token = None
            if 'token=' in query_string:
                token = query_string.split('token=')[1].split('&')[0]
            
            # Reject if no token
            if not token:
                await self.close(code=4001)  # Custom close code for authentication failure
                return
            
            # Get profile from token
            self.profile = await self._get_profile_from_token(token)
            if not self.profile:
                await self.close(code=4001)  # Authentication failed
                return
            
            # Check if conversation exists and profile is a participant
            try:
                conversation = await sync_to_async(Conversation.objects.get)(id=self.conversation_id)
                is_participant = await sync_to_async(
                    lambda: conversation.participants.filter(id=self.profile.id).exists()
                )()
                
                if not is_participant:
                    # Profile is not a participant in this conversation
                    await self.close(code=4003)  # Custom close code for permission denied
                    return
                    
            except Conversation.DoesNotExist:
                # Conversation does not exist
                await self.close(code=4004)  # Custom close code for not found
                return
            
            # Profile is authenticated and authorized - accept the connection
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            
        except Exception as e:
            # Catch any unexpected errors during connection
            # Log the error for debugging (in production, use proper logging)
            await self.close(code=4000)  # Generic error code

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        Remove the channel from the conversation group to stop receiving messages.
        """
        # Remove channel from group when user disconnects
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages - both chat messages and read receipts"""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            # Invalid JSON format
            await self.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
            return
        
        try:
            # Check message type and route accordingly
            message_type = data.get("type")
            
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
            
            # Otherwise, it's a regular chat message - validate content
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
            
            # Optional: Limit message length (e.g., 5000 characters)
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
                content=message_content.strip()  # Strip whitespace before saving
            )

            sender_name = await sync_to_async(lambda: self.profile.get_profile_data.name if self.profile else "anonymous")()

            # Broadcast message to all participants in the conversation
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message", 
                    "message_id": new_message.id,
                    "sender_id": self.profile.id,
                    "sender_name": sender_name,
                    "content": message_content,
                    "timestamp": str(new_message.timestamp),
                    "is_owner": True if self.profile.id == new_message.sender.id else False
                }
            )
        except Conversation.DoesNotExist:
            await self.send(json.dumps({
                "type": "error",
                "message": "Conversation not found"
            }))
        except Exception as e:
            # Log the error for debugging (in production, use proper logging)
            await self.send(json.dumps({
                "type": "error",
                "message": "Failed to send message. Please try again."
            }))

    async def mark_message_read(self, data):
        """Mark a message as read and broadcast read receipt"""
        try:
            message_id = data.get("message_id")
            
            # Validate message_id exists
            if not message_id:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "message_id is required for read receipts"
                }))
                return
            
            # Validate message_id is an integer (or can be converted to one)
            try:
                message_id = int(message_id)
            except (ValueError, TypeError):
                await self.send(json.dumps({
                    "type": "error",
                    "message": "message_id must be a valid integer"
                }))
                return
            
            from .models import Message

            # Ensure the message exists and belongs to this conversation
            target_message = await sync_to_async(
                lambda: Message.objects.get(id=message_id, conversation_id=self.conversation_id)
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

            reader_name = await sync_to_async(lambda: self.profile.get_profile_data.name if self.profile else "anonymous")()
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
        except Message.DoesNotExist:
            await self.send(json.dumps({
                "type": "error",
                "message": f"Message {message_id} not found in this conversation"
            }))
        except Exception as e:
            await self.send(json.dumps({
                "type": "error",
                "message": "Failed to mark message as read"
            }))

    async def handle_typing_indicator(self, data):
        """
        Handle typing indicator events.
        Broadcasts to other participants when user is typing or stops typing.
        Does not save to database - ephemeral event only.
        """
        try:
            is_typing = data.get("is_typing", False)
            
            # Validate is_typing is a boolean
            if not isinstance(is_typing, bool):
                await self.send(json.dumps({
                    "type": "error",
                    "message": "is_typing must be a boolean value"
                }))
                return
            
            # Broadcast typing indicator to all participants in the conversation
            user_name = await sync_to_async(lambda: self.profile.get_profile_data.name if self.profile else "anonymous")()
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
            # Typing indicators are non-critical, fail silently
            # In production, log this for monitoring
            pass

    async def handle_edit_message(self, data):
        """
        Handle message editing.
        Only the sender can edit their own messages.
        """
        try:
            message_id = data.get("message_id")
            # Accept both 'content' and 'new_content' for backward compatibility
            new_content = data.get("content") or data.get("new_content")
            
            # Validate message_id
            if not message_id:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "message_id is required for editing"
                }))
                return
            
            # Convert to integer
            try:
                message_id = int(message_id)
            except (ValueError, TypeError):
                await self.send(json.dumps({
                    "type": "error",
                    "message": "message_id must be a valid integer"
                }))
                return
            
            # Validate new content
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
            
            msg, error = await self._edit_message_sync(message_id, self.profile.id, new_content)
            if error:
                await self.send(json.dumps({
                    "type": "error",
                    "message": error
                }))
                return
            
            # Broadcast edit to all participants, include full message context for immediate UI updates
            editor_name = await sync_to_async(lambda: self.profile.get_profile_data.name if self.profile else "anonymous")()
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
            
        except Message.DoesNotExist:
            await self.send(json.dumps({
                "type": "error",
                "message": f"Message {message_id} not found"
            }))
        except Exception as e:
            await self.send(json.dumps({
                "type": "error",
                "message": "Failed to edit message",
                "error": str(e)
            }))

    async def handle_delete_message(self, data):
        """
        Handle message deletion (soft delete).
        Only the sender can delete their own messages.
        """
        try:
            message_id = data.get("message_id")
            
            # Validate message_id
            if not message_id:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "message_id is required for deletion"
                }))
                return
            
            # Convert to integer
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
            
            # Broadcast deletion to all participants with message context for UI updates
            deleter_name = await sync_to_async(lambda: self.profile.get_profile_data.name if self.profile else "anonymous")()
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
            
        except Message.DoesNotExist:
            await self.send(json.dumps({
                "type": "error",
                "message": f"Message {message_id} not found"
            }))
        except Exception as e:
            await self.send(json.dumps({
                "type": "error",
                "message": "Failed to delete message",
                "error": str(e)
            }))

    async def read_receipt(self, event):
        """Send read receipt to WebSocket clients"""
        await self.send(json.dumps(event))

    async def typing_indicator(self, event):
        """
        Send typing indicator to WebSocket clients.
        Only send to OTHER participants (not the typer themselves).
        """
        # Don't send typing indicator back to the person who is typing
        if event.get("profile_id") != self.profile.id:
            await self.send(json.dumps({
                "type": "typing",
                "profile_id": event.get("profile_id"),
                "username": event.get("username"),
                "is_typing": event.get("is_typing")
            }))

    async def chat_message(self, event):
        """Send chat message to WebSocket clients"""
        await self.send(json.dumps(event))

    async def message_edited(self, event):
        """Send message edit notification to WebSocket clients"""
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

    async def message_deleted(self, event):
        """Send message deletion notification to WebSocket clients"""
        await self.send(json.dumps({
            "type": "delete",
            "message_id": event.get("message_id"),
            "deleter_id": event.get("deleter_id"),
            "deleter_name": event.get("deleter_name"),
            "sender_id": event.get("sender_id"),
            "timestamp": event.get("timestamp"),
            "is_deleted": event.get("is_deleted", True),
        }))
