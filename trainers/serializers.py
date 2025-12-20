from rest_framework import serializers

from accounts.models import Account
from .models import (
    Trainer,
    TrainerCalendarSlot,
    TrainerSpecialization,
    TrainerExperience,
)
import re
from utils.views import get_account_from_token, get_profile_id_from_token


class TrainerSerializer(serializers.ModelSerializer):
    # Accept account_id from frontend, convert to profile_id internally
    class Meta:
        model = Trainer
        fields = [
            "name",
            "bio",
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
        if value:
            if not re.match(r"^\+?\d{7,20}$", value):
                raise serializers.ValidationError(
                    "Enter a valid phone number (digits, optional leading '+')."
                )
        return value

    def create(self, validated_data):
        # Get account_id and find the trainer profile
        account = get_account_from_token(self.context.get("request"))
        # Check if trainer already exists for this profile
        profile_id = get_profile_id_from_token(self.context.get("request"))

        trainer_profile = account.profiles.filter(
            profile_type="trainer", pk=profile_id
        ).first()

        if not trainer_profile:
            raise serializers.ValidationError(
                "No trainer profile found for this account."
            )

        if Trainer.objects.filter(profile_id=trainer_profile).exists():
            raise serializers.ValidationError(
                "Trainer already exists for this account."
            )

        trainer = Trainer(profile_id=trainer_profile, **validated_data)
        trainer.full_clean()
        trainer.save()
        return trainer

    def update(self, instance, validated_data):

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance


class TrainerSpecializationSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TrainerSpecialization
        fields = [
            "account_id",
            "specialization",
            "years_of_experience",
            "hourly_rate",
            "service_location",
        ]

    def validate_account_id(self, value):
        # Get the account
        try:
            account = Account.objects.get(pk=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist.")

        # Find trainer profile from the account
        trainer_profile = account.profiles.filter(profile_type="trainer").first()
        if not trainer_profile:
            raise serializers.ValidationError(
                'Account must have a profile with profile_type="trainer".'
            )

        # Check if trainer exists for this profile
        if not Trainer.objects.filter(profile_id=trainer_profile).exists():
            raise serializers.ValidationError(
                "Trainer does not exist for this account."
            )

        return value

    def validate(self, data):
        # Check if any trainer under this account already has this specialization
        account_id = data.get("account_id")
        specialization = data.get("specialization")

        if account_id and specialization:
            account = Account.objects.get(pk=account_id)
            trainer_profile = account.profiles.filter(profile_type="trainer").first()
            trainer = Trainer.objects.filter(profile_id=trainer_profile).first()

            # Check if this trainer already has this specialization
            if TrainerSpecialization.objects.filter(
                trainer=trainer, specialization=specialization
            ).exists():
                raise serializers.ValidationError(
                    {"specialization": "This trainer already has this specialization."}
                )

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
        # Get account_id and find the trainer
        account_id = validated_data.pop("account_id")
        account = Account.objects.get(pk=account_id)
        trainer_profile = account.profiles.filter(profile_type="trainer").first()
        trainer = Trainer.objects.get(profile_id=trainer_profile)

        # Create specialization with the trainer
        specialization = TrainerSpecialization(trainer=trainer, **validated_data)
        specialization.full_clean()
        specialization.save()
        return specialization

    def update(self, instance, validated_data):
        # Remove account_id if provided (shouldn't update the trainer relationship)
        validated_data.pop("account_id", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance


class TrainerExperienceSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(write_only=True)
    end_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = TrainerExperience
        fields = [
            "account_id",
            "work_place",
            "position",
            "start_date",
            "end_date",
            "description",
        ]

    def validate_account_id(self, value):
        # Get the account
        try:
            account = Account.objects.get(pk=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist.")

        # Find trainer profile from the account
        trainer_profile = account.profiles.filter(profile_type="trainer").first()
        if not trainer_profile:
            raise serializers.ValidationError(
                'Account must have a profile with profile_type="trainer".'
            )

        # Check if trainer exists for this profile
        if not Trainer.objects.filter(profile_id=trainer_profile).exists():
            raise serializers.ValidationError(
                "Trainer does not exist for this account."
            )

        return value

    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be earlier than start date."}
            )

        return data

    def create(self, validated_data):
        # Get account_id and find the trainer
        account_id = validated_data.pop("account_id")
        account = Account.objects.get(pk=account_id)
        trainer_profile = account.profiles.filter(profile_type="trainer").first()
        trainer = Trainer.objects.get(profile_id=trainer_profile)

        # Create experience with the trainer
        experience = TrainerExperience(trainer=trainer, **validated_data)
        experience.full_clean()
        experience.save()
        return experience

    def update(self, instance, validated_data):
        # Remove account_id if provided (shouldn't update the trainer relationship)
        validated_data.pop("account_id", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance


class TrainerCalendarSlotSerializer(serializers.ModelSerializer):
    trainer_id = serializers.PrimaryKeyRelatedField(
        queryset=Trainer.objects.all(),
        write_only=True,
        required=False,
        help_text="Only superusers may set this field.",
    )

    class Meta:
        model = TrainerCalendarSlot
        fields = [
            "slot_start_time",
            "slot_end_time",
            "is_available",
            "trainer_id",
        ]
        read_only_fields = ["is_available",]

    def create(self, validated_data):
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("Request context is required.")

        user = request.user
        if not user.is_superuser:
            # For non-superusers, set trainer based on their profile
            profile_id = get_profile_id_from_token(request)
            trainer_profile = user.profiles.filter(
                profile_type="trainer", pk=profile_id
            ).first()
            if not trainer_profile:
                raise serializers.ValidationError(
                    "No trainer profile found for this account."
                )
            trainer = Trainer.objects.filter(profile_id=trainer_profile).first()
            if not trainer:
                raise serializers.ValidationError(
                    "No trainer found for this profile."
                )
            validated_data["trainer"] = trainer
        else:
            # For superusers, use the provided trainer_id
            trainer = validated_data.pop("trainer_id", None)
            if not trainer:
                raise serializers.ValidationError(
                    "trainer_id is required for superusers."
                )
            validated_data["trainer"] = trainer

        slot = TrainerCalendarSlot(**validated_data)
        slot.full_clean()
        slot.save()
        return slot
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance
    
    
