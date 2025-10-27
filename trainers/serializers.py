from rest_framework import serializers
from .models import Trainer

class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = ['profile_id', 'name', 'specialty', 'created_at', 'updated_at']