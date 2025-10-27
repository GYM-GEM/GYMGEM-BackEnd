from rest_framework import serializers
from .models import Trainee

class TraineeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainee
        fields = ['profile_id', 'name', 'age', 'created_at', 'updated_at']