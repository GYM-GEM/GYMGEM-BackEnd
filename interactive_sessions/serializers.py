from rest_framework import serializers
from interactive_sessions.models import InteractiveSession
from trainers.models import TrainerCalendarSlot
from profiles.models import Profile


class InteractiveSessionSerializer(serializers.ModelSerializer):
    scheduled_at = serializers.PrimaryKeyRelatedField(
        queryset=TrainerCalendarSlot.objects.all()
    )
    first_participant = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(), many=True, required=False
    )
    second_participant = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(), many=True, required=False
    )

    class Meta:
        model = InteractiveSession
        fields = [
            'id',
            'session_title',
            'description',
            'status',
            'scheduled_at',
            'first_participant',
            'second_participant',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
