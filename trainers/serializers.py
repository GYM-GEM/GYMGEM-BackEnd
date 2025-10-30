from rest_framework import serializers
from .models import Trainer
from profiles.models import Profile
import re

class TrainerSerializer(serializers.ModelSerializer):
    # represent profile as PK but accept/validate Profile instance
    profile_id = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all())
    profile_picture = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    birthdate = serializers.DateField(required=False)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = Trainer
        fields = [
            "profile_id",
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

    def validate_profile_id(self, value: Profile):
        # ensure the linked profile is of type 'trainer'
        if getattr(value, "profile_type", None) != "trainer":
            raise serializers.ValidationError('Profile must have profile_type="trainer" to create a Trainer.')
        return value

    def validate_phone_number(self, value):
        if value:
            if not re.match(r'^\+?\d{7,20}$', value):
                raise serializers.ValidationError("Enter a valid phone number (digits, optional leading '+').")
        return value

    def create(self, validated_data):
        profile = validated_data.get("profile_id")
        if Trainer.objects.filter(profile_id=profile).exists():
            raise serializers.ValidationError({"profile_id": "Trainer already exists for this profile."})
        trainer = Trainer(**validated_data)
        trainer.full_clean()
        trainer.save()
        return trainer

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance