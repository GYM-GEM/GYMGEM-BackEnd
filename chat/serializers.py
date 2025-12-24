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
    sender_name = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'content', 'attachment',
                  'timestamp', 'is_read', 'read_at', 'is_deleted', 'edited_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    other_participant_id = serializers.SerializerMethodField(read_only=True)
    other_participant_name = serializers.SerializerMethodField(read_only=True)
    other_participant_profile_picture = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)
    unread_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id',
            'messages',
            'created_at',
            'other_participant_id',
            'other_participant_name',
            'other_participant_profile_picture',
            'last_message',
            'unread_count',
        ]

    def _get_other_participant(self):
        request = self.context.get('request')
        if not request:
            return None
        profile_id = get_profile_id_from_token(request)
        if not profile_id:
            return None
        return self.instance.participants.exclude(id=profile_id).first()

    def get_other_participant_id(self, obj):  # pylint: disable=unused-argument
        other = self._get_other_participant()
        return getattr(other, 'id', None)

    def get_other_participant_name(self, obj):  # pylint: disable=unused-argument
        other = self._get_other_participant()
        return _get_profile_display_name(other)

    def get_other_participant_profile_picture(self, obj):  # pylint: disable=unused-argument
        other = self._get_other_participant()
        return _get_profile_picture(other)

    def get_last_message(self, obj):  # pylint: disable=unused-argument
        last_msg = self.instance.messages.order_by('-timestamp').first()
        if not last_msg:
            return None
        return MessageSerializer(last_msg, context=self.context).data

    def get_unread_count(self, obj):  # pylint: disable=unused-argument
        request = self.context.get('request')
        if not request:
            return 0
        profile_id = get_profile_id_from_token(request)
        if not profile_id:
            return 0
        profile = Profile.objects.filter(id=profile_id).first()
        if not profile:
            return 0
        return self.instance.messages.filter(is_read=False).exclude(sender=profile).count()
    
