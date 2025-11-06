from rest_framework import serializers

from accounts.models import Account
from .models import Trainer, TrainerSpecialization, TrainerExperience
from profiles.models import Profile
import re

class TrainerSerializer(serializers.ModelSerializer):
    # Accept account_id from frontend, convert to profile_id internally
    account_id = serializers.IntegerField(write_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    birthdate = serializers.DateField(required=False)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = Trainer
        fields = [
            "account_id",
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

    def validate_account_id(self, value):
        # Get the account
        try:
            account = Account.objects.get(pk=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist.")
        
        # Find trainer profile from the account
        trainer_profile = account.profiles.filter(profile_type="trainer").first()
        if not trainer_profile:
            raise serializers.ValidationError('Account must have a profile with profile_type="trainer".')
        
        return value

    def validate_phone_number(self, value):
        if value:
            if not re.match(r'^\+?\d{7,20}$', value):
                raise serializers.ValidationError("Enter a valid phone number (digits, optional leading '+').")
        return value

    def create(self, validated_data):
        # Get account_id and find the trainer profile
        account_id = validated_data.pop("account_id")
        account = Account.objects.get(pk=account_id)
        trainer_profile = account.profiles.filter(profile_type="trainer").first()
        
        # Check if trainer already exists for this profile
        if Trainer.objects.filter(profile_id=trainer_profile).exists():
            raise serializers.ValidationError({"account_id": "Trainer already exists for this account."})
        
        # Create trainer with the found profile
        trainer = Trainer(profile_id=trainer_profile, **validated_data)
        trainer.full_clean()
        trainer.save()
        return trainer

    def update(self, instance, validated_data):
        # Remove account_id if provided (shouldn't update the profile relationship)
        validated_data.pop("account_id", None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance
    
class TrainerSpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerSpecialization
        fields = [
            "trainer",
            "specialization",
            "years_of_experience",
            "hourly_rate",
            "service_location",
        ]
    def validate(self, data):
        # Check if this trainer already has this specialization
        trainer = data.get('trainer')
        specialization = data.get('specialization')
        if TrainerSpecialization.objects.filter(
            trainer=trainer,
            specialization=specialization
        ).exists():
            raise serializers.ValidationError({"specialization": "This trainer already has this specialization."})  
        return data
    def validate_years_of_experience(self, value):
        if value < 0:
            raise serializers.ValidationError("Years of experience cannot be negative.")
        return value
    def validate_hourly_rate(self, value):
        if value < 0:
            raise serializers.ValidationError("Hourly rate cannot be negative.")
        return value
    def create(self, validated_data):
        specialization = TrainerSpecialization(**validated_data)
        specialization.full_clean()
        specialization.save()
        return specialization
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance
    
class TrainerExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerExperience
        fields = [
            "trainer",
            "work_place",
            "position",
            "start_date",
            "end_date",
            "description",
        ]
    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be earlier than start date."})
        
        trainer = data.get('trainer')
        if TrainerExperience.objects.filter(trainer=trainer).exists():
            raise serializers.ValidationError({"non_field_errors": "This trainer already has recorded experience at this workplace with this position."})
        return data
    def create(self, validated_data):
        experience = TrainerExperience(**validated_data)
        experience.full_clean()
        experience.save()
        return experience
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance