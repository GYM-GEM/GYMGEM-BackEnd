from rest_framework import serializers
from .models import Trainer
from profiles.models import Profile

class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = ['profile_id', 'name', 'specialty', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_profile_id(self, value: Profile):
        if value.profile_type != 'trainer':
            raise serializers.ValidationError('Profile must have profile_type="trainer" to create a Trainer.')
        return value

    def create(self, validated_data):
        instance = Trainer(**validated_data)
        instance.full_clean()
        instance.save()
        return instance