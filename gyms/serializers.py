from rest_framework import serializers
from .models import Gym
from profiles.models import Profile

class GymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = ['profile_id', 'name', 'location', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_profile_id(self, value: Profile):
        if value.profile_type != 'gym':
            raise serializers.ValidationError('Profile must have profile_type="gym" to create a Gym.')
        return value

    def create(self, validated_data):
        instance = Gym(**validated_data)
        instance.full_clean()
        instance.save()
        return instance