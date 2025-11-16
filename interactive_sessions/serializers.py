
from rest_framework import serializers
from interactive_sessions.models import InteractiveSession


class InteractiveSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteractiveSession
        fields = [
            "id",
            "session_title",
            "description",
            "scheduled_at",
            "first_participant",
            "second_participant",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def create(self, validated_data):
        first_participant = validated_data.pop("first_participant", None)
        second_participant = validated_data.pop("second_participant", None)
        session = InteractiveSession.objects.create(**validated_data)
        if first_participant:
            session.participants.add(first_participant)
        if second_participant:
            session.participants.add(second_participant)
        session.full_clean()
        session.save()
        return session
