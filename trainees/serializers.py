from rest_framework import serializers
from accounts.models import Account
from .models import Trainee
from profiles.models import Profile
import re

class TraineeSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(write_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    birthdate = serializers.DateField(required=False)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = Trainee
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
        try:
            account = Account.objects.get(pk=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist.")

        # Use reverse name that exists; if not sure, query Profile directly
        trainee_profile = account.profiles.filter(profile_type="trainee").first() 
        if not trainee_profile:
            raise serializers.ValidationError('Account must have a profile with profile_type="trainee".')

        return value

    def validate_phone_number(self, value):
        if value and not re.match(r'^\+?\d{7,20}$', value):
            raise serializers.ValidationError("Enter a valid phone number (digits, optional leading '+').")
        return value

    def create(self, validated_data):
        account_id = validated_data.pop("account_id")
        account = Account.objects.get(pk=account_id)
        trainee_profile = account.profiles.filter(profile_type="trainee").first() 
    
        # prevent duplicates
        if Trainee.objects.filter(profile_id=trainee_profile).exists():
            raise serializers.ValidationError({"account_id": "Trainee already exists for this account."})

        trainee = Trainee(profile_id=trainee_profile, **validated_data)
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