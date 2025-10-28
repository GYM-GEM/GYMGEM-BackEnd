from rest_framework import serializers
from .models import Store
from profiles.models import Profile

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['profile_id', 'name', 'location', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_profile_id(self, value: Profile):
        # Ensure the selected profile is actually of type 'store'
        if value.profile_type != 'store':
            raise serializers.ValidationError('Profile must have profile_type="store" to create a Store.')
        return value

    def create(self, validated_data):
        # Let model-level validation run too for defense in depth
        instance = Store(**validated_data)
        instance.full_clean()
        instance.save()
        return instance