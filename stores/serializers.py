from rest_framework import serializers
from accounts.models import Account
from .models import Store , StoreBranch
from profiles.models import Profile 

class StoreSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Store
        fields = ['account_id', 'name', 'profile_picture','description','store_type', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_account_id(self, value):
        # Get the account
        try:
            account = Account.objects.get(pk=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist.")

        # Find store profile from the account
        store_profile = account.profiles.filter(profile_type="store").first() if hasattr(account, 'profiles') else Profile.objects.filter(account=account, profile_type="store").first()
        if not store_profile:
            raise serializers.ValidationError(
                'Account must have a profile with profile_type="store".'
            )

        return value

    def create(self, validated_data):
        # Get account_id and find the store profile
        account_id = validated_data.pop("account_id")
        account = Account.objects.get(pk=account_id)
        store_profile = account.profiles.filter(profile_type="store").first() if hasattr(account, 'profiles') else Profile.objects.filter(account=account, profile_type="store").first()

        if not store_profile:
            raise serializers.ValidationError({"account_id": "Account does not have a store profile."})

        # Check if store already exists for this profile
        if Store.objects.filter(profile_id=store_profile).exists():
            raise serializers.ValidationError(
                {"account_id": "Store already exists for this account."}
            )

        # Create store with the found profile
        store = Store(profile_id=store_profile, **validated_data)
        store.full_clean()
        store.save()
        return store

    
    def update(self, instance, validated_data):
        # Remove account_id if provided (shouldn't update the profile relationship)
        validated_data.pop("account_id", None)

        # Update the instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()  # Ensure model validation is run
        instance.save()
        return instance
    
class StoreBranchSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = StoreBranch
        fields = ['account_id', 'store_id', 'opening_time', 'closing_time', 'country', 'state', 'street', 'zip_code', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_account_id(self, value):
        # Get the account
        try:
            account = Account.objects.get(pk=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist.")

        # Find store profile from the account
        store_profile = account.profiles.filter(profile_type="store").first() if hasattr(account, 'profiles') else Profile.objects.filter(account=account, profile_type="store").first()
        if not store_profile:
            raise serializers.ValidationError(
                'Account must have a profile with profile_type="store".'
            )

        return value
    def create(self, validated_data):
        # Get account_id and find the store profile
        account_id = validated_data.pop("account_id")
        account = Account.objects.get(pk=account_id)
        store_profile = account.profiles.filter(profile_type="store").first() if hasattr(account, 'profiles') else Profile.objects.filter(account=account, profile_type="store").first()

        if not store_profile:
            raise serializers.ValidationError({"account_id": "Account does not have a store profile."})

        # Create store branch with the found profile
        store_branch = StoreBranch(**validated_data)
        store_branch.full_clean()
        store_branch.save()
        return store_branch
    def update(self, instance, validated_data):
        # Remove account_id if provided (shouldn't update the profile relationship)
        validated_data.pop("account_id", None)

        # Update the instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()  # Ensure model validation is run
        instance.save()
        return instance