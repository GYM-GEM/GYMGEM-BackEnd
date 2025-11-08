from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Conversation, Message
import json

User = get_user_model()


class ConversationModelTest(TestCase):
    """Test the Conversation model"""

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@test.com', password='pass123')
        self.user2 = User.objects.create_user(username='user2', email='user2@test.com', password='pass123')

    def test_create_conversation(self):
        """Test creating a conversation between two users"""
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())
        self.assertIsNotNone(conversation.created_at)

    def test_conversation_str(self):
        """Test conversation string representation"""
        conversation = Conversation.objects.create()
        self.assertEqual(str(conversation), f"Conversation {conversation.id}")


class MessageModelTest(TestCase):
    """Test the Message model"""

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@test.com', password='pass123')
        self.user2 = User.objects.create_user(username='user2', email='user2@test.com', password='pass123')
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

    def test_create_message(self):
        """Test creating a message"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Hello, this is a test message"
        )
        
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, "Hello, this is a test message")
        self.assertFalse(message.is_read)
        self.assertFalse(message.is_deleted)
        self.assertIsNone(message.edited_at)
        self.assertIsNotNone(message.timestamp)

    def test_message_soft_delete(self):
        """Test soft deleting a message"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Message to delete"
        )
        
        message.is_deleted = True
        message.content = ""
        message.save()
        
        self.assertTrue(message.is_deleted)
        self.assertEqual(message.content, "")

    def test_message_edit(self):
        """Test editing a message"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Original content"
        )
        
        from django.utils.timezone import now
        message.content = "Edited content"
        message.edited_at = now()
        message.save()
        
        self.assertEqual(message.content, "Edited content")
        self.assertIsNotNone(message.edited_at)


class ConversationAPITest(APITestCase):
    """Test the Conversation REST API endpoints"""

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@test.com', password='pass123')
        self.user2 = User.objects.create_user(username='user2', email='user2@test.com', password='pass123')
        self.user3 = User.objects.create_user(username='user3', email='user3@test.com', password='pass123')
        
        # Get JWT token for user1
        refresh = RefreshToken.for_user(self.user1)
        self.token = str(refresh.access_token)
        
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_start_conversation(self):
        """Test starting a new conversation"""
        url = '/api/chat/conversations/start/'
        data = {'user2': self.user2.id}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        
        conversation = Conversation.objects.get(id=response.data['id'])
        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())

    def test_start_conversation_duplicate(self):
        """Test starting a conversation that already exists returns existing conversation"""
        # Create first conversation
        url = '/api/chat/conversations/start/'
        data = {'user2': self.user2.id}
        response1 = self.client.post(url, data, format='json')
        
        # Try to create duplicate
        response2 = self.client.post(url, data, format='json')
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['id'], response2.data['id'])

    def test_start_conversation_with_self(self):
        """Test that user cannot start conversation with themselves"""
        url = '/api/chat/conversations/start/'
        data = {'user2': self.user1.id}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_conversations(self):
        """Test listing user's conversations"""
        # Create conversations
        conv1 = Conversation.objects.create()
        conv1.participants.add(self.user1, self.user2)
        
        conv2 = Conversation.objects.create()
        conv2.participants.add(self.user1, self.user3)
        
        # Conversation user1 is not in
        conv3 = Conversation.objects.create()
        conv3.participants.add(self.user2, self.user3)
        
        url = '/api/chat/conversations/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only user1's conversations

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access conversations"""
        self.client.credentials()  # Remove authentication
        
        url = '/api/chat/conversations/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MessageAPITest(APITestCase):
    """Test the Message REST API endpoints"""

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@test.com', password='pass123')
        self.user2 = User.objects.create_user(username='user2', email='user2@test.com', password='pass123')
        
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
        
        # Get JWT token for user1
        refresh = RefreshToken.for_user(self.user1)
        self.token = str(refresh.access_token)
        
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_create_message(self):
        """Test creating a message via REST API"""
        url = '/api/chat/messages/'
        data = {
            'conversation': self.conversation.id,
            'sender': self.user1.id,
            'content': 'Test message via REST API'
        }
        
        # Use multipart format for MessageViewSet
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Test message via REST API')
        self.assertEqual(response.data['sender'], self.user1.id)

    def test_list_messages_pagination(self):
        """Test listing messages with pagination"""
        # Create multiple messages
        for i in range(5):
            Message.objects.create(
                conversation=self.conversation,
                sender=self.user1,
                content=f"Message {i}"
            )
        
        url = '/api/chat/messages/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have pagination
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)

    def test_mark_message_read(self):
        """Test marking a message as read"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user2,
            content="Unread message"
        )
        
        url = f'/api/chat/messages/{message.id}/mark_read/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        message.refresh_from_db()
        self.assertTrue(message.is_read)
        self.assertIsNotNone(message.read_at)

    def test_edit_message(self):
        """Test editing a message (only sender can edit)"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Original message"
        )
        
        url = f'/api/chat/messages/{message.id}/edit/'
        data = {'content': 'Edited message'}
        # Use multipart format since MessageViewSet uses MultiPartParser
        response = self.client.patch(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        message.refresh_from_db()
        self.assertEqual(message.content, 'Edited message')
        self.assertIsNotNone(message.edited_at)

    def test_edit_message_not_sender(self):
        """Test that only sender can edit their message"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user2,  # Different user
            content="Someone else's message"
        )
        
        url = f'/api/chat/messages/{message.id}/edit/'
        data = {'content': 'Trying to edit'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_soft_delete_message(self):
        """Test soft-deleting a message"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Message to delete"
        )
        
        url = f'/api/chat/messages/{message.id}/soft_delete/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        message.refresh_from_db()
        self.assertTrue(message.is_deleted)
        self.assertEqual(message.content, "")

    def test_soft_delete_message_not_sender(self):
        """Test that only sender can delete their message"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user2,  # Different user
            content="Someone else's message"
        )
        
        url = f'/api/chat/messages/{message.id}/soft_delete/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_edit_deleted_message(self):
        """Test that deleted messages cannot be edited"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Message to delete"
        )
        
        # Delete the message first
        message.is_deleted = True
        message.content = ""
        message.save()
        
        # Try to edit it
        url = f'/api/chat/messages/{message.id}/edit/'
        data = {'content': 'Trying to edit deleted message'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
