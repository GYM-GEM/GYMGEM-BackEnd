from rest_framework import serializers
from utils.views import get_profile_id_from_token
from profiles.models import Profile
from .models import Conversation, Message


def _get_profile_display_name(profile):
    """Return a human friendly name for the profile if available."""
    if not profile:
        return None

    trainer = getattr(profile, 'trainer', None)
    if trainer and getattr(trainer, 'name', None):
        return trainer.name

    trainee = getattr(profile, 'trainee', None)
    if trainee and getattr(trainee, 'name', None):
        return trainee.name

    gym = getattr(profile, 'gym', None)
    if gym and getattr(gym, 'name', None):
        return gym.name

    store = getattr(profile, 'store', None)
    if store and getattr(store, 'name', None):
        return store.name

    account = getattr(profile, 'account', None)
    if account and getattr(account, 'username', None):
        return account.username

    return None


def _get_profile_picture(profile):
    """Return a profile picture URL if the profile has one."""
    if not profile:
        return None

    trainer = getattr(profile, 'trainer', None)
    if trainer and getattr(trainer, 'profile_picture', None):
        return trainer.profile_picture

    trainee = getattr(profile, 'trainee', None)
    if trainee and getattr(trainee, 'profile_picture', None):
        return trainee.profile_picture

    gym = getattr(profile, 'gym', None)
    if gym and getattr(gym, 'profile_picture', None):
        return gym.profile_picture

    store = getattr(profile, 'store', None)
    if store and getattr(store, 'profile_picture', None):
        return store.profile_picture

    return None

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'content', 'attachment',
                  'timestamp', 'is_read', 'read_at', 'is_deleted', 'edited_at']

    def get_sender_name(self, obj):
        return _get_profile_display_name(obj.sender)


class ConversationSerializer(serializers.ModelSerializer):
    other_participant_id = serializers.SerializerMethodField(read_only=True)
    other_participant_name = serializers.SerializerMethodField(read_only=True)
    other_participant_profile_picture = serializers.SerializerMethodField(read_only=True)
    other_participant_role = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)
    last_message_timestamp = serializers.SerializerMethodField(read_only=True)
    unread_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id',
            'other_participant_id',
            'other_participant_name',
            'other_participant_profile_picture',
            'other_participant_role',
            'last_message',
            'last_message_timestamp',
            'unread_count',
        ]

    def _get_other_participant(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        profile_id = get_profile_id_from_token(request)
        if not profile_id:
            return None
        return obj.participants.exclude(id=profile_id).first()

    def get_other_participant_id(self, obj):
        other = self._get_other_participant(obj)
        return getattr(other, 'id', None)

    def get_other_participant_name(self, obj):
        other = self._get_other_participant(obj)
        return _get_profile_display_name(other)

    def get_other_participant_profile_picture(self, obj):
        other = self._get_other_participant(obj)
        return _get_profile_picture(other)

    def get_other_participant_role(self, obj):
        other = self._get_other_participant(obj)
        if not other:
            return None
        if hasattr(other, 'trainer'):
            return 'trainer'
        elif hasattr(other, 'trainee'):
            return 'trainee'
        elif hasattr(other, 'gym'):
            return 'gym'
        elif hasattr(other, 'store'):
            return 'store'
        return 'unknown'
    
    def get_last_message(self, obj):
        # Sort prefetched messages in Python instead of queryset to use prefetched data
        messages = list(obj.messages.all())
        if not messages:
            return None
        # Sort by timestamp descending and get the first one
        last_msg = max(messages, key=lambda m: m.timestamp)
        return MessageSerializer(last_msg, context=self.context).data

    def get_last_message_timestamp(self, obj):
        messages = list(obj.messages.all())
        if not messages:
            return None
        last_msg = max(messages, key=lambda m: m.timestamp)
        return last_msg.timestamp

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        profile_id = get_profile_id_from_token(request)
        if not profile_id:
            return 0
        profile = Profile.objects.filter(id=profile_id).first()
        if not profile:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=profile).count()

