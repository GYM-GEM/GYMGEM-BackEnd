import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message, Conversation
from django.utils.timezone import now
from django.contrib.auth.models import AnonymousUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
            self.room_group_name = f'chat_{self.conversation_id}'
            
            # Get the user from scope (set by JWTAuthMiddleware)
            user = self.scope.get('user')
            
            # Reject unauthenticated users
            if not user or isinstance(user, AnonymousUser):
                await self.close(code=4001)  # Custom close code for authentication failure
                return
            
            # Check if conversation exists and user is a participant
            try:
                conversation = await sync_to_async(Conversation.objects.get)(id=self.conversation_id)
                is_participant = await sync_to_async(
                    lambda: conversation.participants.filter(id=user.id).exists()
                )()
                
                if not is_participant:
                    # User is not a participant in this conversation
                    await self.close(code=4003)  # Custom close code for permission denied
                    return
                    
            except Conversation.DoesNotExist:
                # Conversation does not exist
                await self.close(code=4004)  # Custom close code for not found
                return
            
            # User is authenticated and authorized - accept the connection
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
            
            sender = self.scope["user"]

            # Save message to database
            convo = await sync_to_async(Conversation.objects.get)(id=self.conversation_id)
            new_message = await sync_to_async(Message.objects.create)(
                conversation=convo, 
                sender=sender, 
                content=message_content.strip()  # Strip whitespace before saving
            )

            # Broadcast message to all participants in the conversation
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message", 
                    "message_id": new_message.id,
                    "sender": sender.username, 
                    "content": message_content,
                    "timestamp": str(new_message.timestamp)
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
            msg = await sync_to_async(Message.objects.get)(id=message_id)
            msg.is_read = True
            msg.read_at = now()
            await sync_to_async(msg.save)()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "read_receipt",
                    "message_id": message_id,
                    "reader": self.scope["user"].username,
                    "read_at": str(msg.read_at)
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
            
            sender = self.scope["user"]
            
            # Broadcast typing indicator to all participants in the conversation
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "username": sender.username,
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
            
            # Get message from database
            msg = await sync_to_async(Message.objects.get)(id=message_id)
            
            # Check if user is the sender
            if msg.sender.id != self.scope["user"].id:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "You can only edit your own messages"
                }))
                return
            
            # Check if message is already deleted
            if msg.is_deleted:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "Cannot edit a deleted message"
                }))
                return
            
            # Update message
            msg.content = new_content.strip()
            msg.edited_at = now()
            await sync_to_async(msg.save)()
            
            # Broadcast edit to all participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "message_edited",
                    "message_id": message_id,
                    "content": new_content.strip(),
                    "edited_at": str(msg.edited_at),
                    "editor": self.scope["user"].username
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
                "message": "Failed to edit message"
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
            
            # Get message from database
            msg = await sync_to_async(Message.objects.get)(id=message_id)
            
            # Check if user is the sender
            if msg.sender.id != self.scope["user"].id:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "You can only delete your own messages"
                }))
                return
            
            # Check if already deleted
            if msg.is_deleted:
                await self.send(json.dumps({
                    "type": "error",
                    "message": "Message is already deleted"
                }))
                return
            
            # Soft delete - mark as deleted but don't remove from database
            msg.is_deleted = True
            msg.content = ""  # Clear content for privacy
            await sync_to_async(msg.save)()
            
            # Broadcast deletion to all participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "message_deleted",
                    "message_id": message_id,
                    "deleter": self.scope["user"].username
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
                "message": "Failed to delete message"
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
        if event.get("username") != self.scope["user"].username:
            await self.send(json.dumps({
                "type": "typing",
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
            "editor": event.get("editor")
        }))

    async def message_deleted(self, event):
        """Send message deletion notification to WebSocket clients"""
        await self.send(json.dumps({
            "type": "delete",
            "message_id": event.get("message_id"),
            "deleter": event.get("deleter")
        }))
