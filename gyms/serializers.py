from rest_framework import serializers
from .models import Gym
from profiles.models import Profile
from accounts.models import Account

class GymSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Gym
        fields = ['account_id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_account_id(self, value):
        # Get the account
        try:
            account = Account.objects.get(pk=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist.")

        # Find gym profile from the account
        gym_profile = account.profiles.filter(profile_type="gym").first() if hasattr(account, 'profiles') else Profile.objects.filter(account=account, profile_type="gym").first()
        if not gym_profile:
            raise serializers.ValidationError(
                'Account must have a profile with profile_type="gym".'
            )

        return value

    def create(self, validated_data):
        # Get account_id and find the gym profile
        account_id = validated_data.pop("account_id")
        account = Account.objects.get(pk=account_id)
        gym_profile = account.profiles.filter(profile_type="gym").first() if hasattr(account, 'profiles') else Profile.objects.filter(account=account, profile_type="gym").first()

        if not gym_profile:
            raise serializers.ValidationError({"account_id": "Account does not have a gym profile."})

        # Check if gym already exists for this profile
        if Gym.objects.filter(profile_id=gym_profile).exists():
            raise serializers.ValidationError(
                {"account_id": "Gym already exists for this account."}
            )

        # Create gym with the found profile
        gym = Gym(profile_id=gym_profile, **validated_data)
        gym.full_clean()
        gym.save()
        return gym

    def update(self, instance, validated_data):
        # Remove account_id if provided (shouldn't update the profile relationship)
        validated_data.pop("account_id", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance
    
class GymBranchSerializer(serializers.ModelSerializer):
    gym_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Gym.Branch
        fields = ['gym_id', 'country', 'state', 'street', 'zip_code', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_gym_id(self, value):
        try:
            gym = Gym.objects.get(pk=value)
        except Gym.DoesNotExist:
            raise serializers.ValidationError("Gym does not exist.")
        return value

    def create(self, validated_data):
        gym_id = validated_data.pop("gym_id")
        gym = Gym.objects.get(pk=gym_id)
        branch = Gym.Branch(gym=gym, **validated_data)
        branch.full_clean()
        branch.save()
        return branch

    def update(self, instance, validated_data):
        validated_data.pop("gym_id", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance