from rest_framework import serializers
from .models import Trainee
from profiles.models import Profile

class TraineeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainee
        fields = ['profile_id', 'name', 'age', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_profile_id(self, value: Profile):
        if value.profile_type != 'trainee':
            raise serializers.ValidationError('Profile must have profile_type="trainee" to create a Trainee.')
        return value

    def create(self, validated_data):
        instance = Trainee(**validated_data)
        instance.full_clean()
        instance.save()
        return instance