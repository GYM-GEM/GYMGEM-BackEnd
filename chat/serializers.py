from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'content', 'attachment',
                  'timestamp', 'is_read', 'read_at', 'is_deleted', 'edited_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'messages', 'created_at']
