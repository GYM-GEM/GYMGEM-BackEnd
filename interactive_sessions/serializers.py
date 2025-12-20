from rest_framework import serializers
from interactive_sessions.models import InteractiveSession
from trainers.models import TrainerCalendarSlot
from profiles.models import Profile


class InteractiveSessionSerializer(serializers.ModelSerializer):
    scheduled_at = serializers.PrimaryKeyRelatedField(
        queryset=TrainerCalendarSlot.objects.all()
    )
    trainer = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.filter(profile_type='trainer'), many=True, required=False
    )
    trainee = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.filter(profile_type='trainee'), many=True, required=False
    )

    class Meta:
        model = InteractiveSession
        fields = [
            'id',
            'session_title',
            'description',
            'status',
            'scheduled_at',
            'trainer',
            'trainee',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

