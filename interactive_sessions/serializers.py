from rest_framework import serializers
from interactive_sessions.models import InteractiveSession
from trainers.models import TrainerCalendarSlot
from profiles.models import Profile


class InteractiveSessionSerializer(serializers.ModelSerializer):
    scheduled_at = serializers.PrimaryKeyRelatedField(
        queryset=TrainerCalendarSlot.objects.all()
    )
    trainer = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.filter(profile_type='trainer'), required=False
    )
    trainee = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.filter(profile_type='trainee'), required=False
    )
    trainee_name = serializers.CharField(read_only=True)
    trainer_name = serializers.CharField(read_only=True)
    starting_time = serializers.DateTimeField(read_only=True)

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
            'trainee_name',
            'trainer_name',
            'starting_time',
            'created_at',
            'updated_at',
            'fees',
            'total_active_minutes',
        ]
        read_only_fields = ['created_at', 'updated_at']

