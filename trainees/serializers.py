from rest_framework import serializers
from accounts.models import Account
from utils.views import get_account_from_token, get_profile_id_from_token
from .models import Trainee, TraineeRecords
from profiles.models import Profile
import re


class TraineeSerializer(serializers.ModelSerializer):
    profile_picture = serializers.URLField(
        required=False, allow_null=True
    )
    birthdate = serializers.DateField(required=False)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = Trainee
        fields = [
            "name",
            "profile_picture",
            "gender",
            "birthdate",
            "country",
            "state",
            "zip_code",
            "phone_number",
            "balance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "balance"]

    def validate_phone_number(self, value):
        if value and not re.match(r"^\+?\d{7,20}$", value):
            raise serializers.ValidationError(
                "Enter a valid phone number (digits, optional leading '+')."
            )
        return value

    def create(self, validated_data):
        # Get account_id and find the trainer profile
        account = get_account_from_token(self.context.get("request"))
        # Check if trainer already exists for this profile
        profile_id = get_profile_id_from_token(self.context.get("request"))
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            raise serializers.ValidationError("Profile not found.")
    

        if Trainee.objects.filter(profile_id=profile).exists():
            raise serializers.ValidationError(
                "Trainee already exists for this account."
            )

        trainee = Trainee(profile_id=profile, **validated_data)
        trainee.full_clean()
        trainee.save()
        return trainee

    def update(self, instance, validated_data):
        validated_data.pop("account_id", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance


class TraineeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TraineeRecords
        fields = [
            "id",
            "record_date",
            "weight",
            "height",
            "body_fat_percentage",
            "muscle_mass",
            "bone_mass",
            "body_water_percentage",
            "BMR",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]