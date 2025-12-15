from rest_framework import serializers
from accounts.models import Account
from .models import Store, StoreBranch, StoreItem,StoreItemInventory, StoreItemSize, Order, OrderItem
from profiles.models import Profile

class StoreSerializer(serializers.ModelSerializer):
    # account_id = serializers.IntegerField(write_only=True)
    profile_id = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Store
        fields = ['profile_id', 'name', 'profile_picture','description','store_type', 'created_at', 'updated_at']
        read_only_fields = ['profile_id', 'created_at', 'updated_at']

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
        fields = ['id', 'account_id', 'store_id', 'opening_time', 'closing_time', 'country', 'state', 'street', 'zip_code', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_account_id(self, value):
        try:
            account = Account.objects.get(pk=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist.")

        store_profile = account.profiles.filter(profile_type="store").first() if hasattr(account, 'profiles') else Profile.objects.filter(account=account, profile_type="store").first()
        if not store_profile:
            raise serializers.ValidationError('Account must have a store profile.')
        return value

    def create(self, validated_data):
        account_id = validated_data.pop("account_id")
        account = Account.objects.get(pk=account_id)
        store_profile = account.profiles.filter(profile_type="store").first() if hasattr(account, 'profiles') else Profile.objects.filter(account=account, profile_type="store").first()

        if not store_profile:
            raise serializers.ValidationError({"account_id": "Account does not have a store profile."})

        store_branch = StoreBranch(**validated_data)
        store_branch.full_clean()
        store_branch.save()
        return store_branch

    def update(self, instance, validated_data):
        validated_data.pop("account_id", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance
    
class StoreItemSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreItemSize
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['created_at']

class StoreItemInventorySerializer(serializers.ModelSerializer):
    size_name = serializers.CharField(source='size_id.name', read_only=True)

    class Meta:
        model = StoreItemInventory
        fields = ['id', 'store_item_id', 'size_id', 'size_name', 'quantity', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value
    
class StoreItemSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(write_only=True)
    inventory = StoreItemInventorySerializer(source='storeiteminventory_set', many=True, read_only=True)
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = StoreItem
        fields = [
            'id', 'account_id', 'store_id', 'branch_id', 'name', 'description',
            'price', 'category', 'brand', 'expiration_date',
            'inventory', 'total_quantity', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'inventory', 'total_quantity']

    def get_total_quantity(self, obj):
        return obj.get_total_quantity()

    def validate_account_id(self, value):
        try:
            account = Account.objects.get(pk=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist.")

        store_profile = account.profiles.filter(profile_type="store").first() if hasattr(account, 'profiles') else Profile.objects.filter(account=account, profile_type="store").first()
        if not store_profile:
            raise serializers.ValidationError('Account must have a store profile.')
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def create(self, validated_data):
        account_id = validated_data.pop("account_id")
        account = Account.objects.get(pk=account_id)
        store_profile = account.profiles.filter(profile_type="store").first() if hasattr(account, 'profiles') else Profile.objects.filter(account=account, profile_type="store").first()

        # Get or verify store
        store_id = validated_data.get('store_id')
        if not store_id or store_id.profile_id != store_profile:
            raise serializers.ValidationError({"store_id": "Store must belong to the authenticated store profile."})

        item = StoreItem(**validated_data)
        item.full_clean()
        item.save()
        return item

    def update(self, instance, validated_data):
        validated_data.pop("account_id", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance

class OrderItemSerializer(serializers.ModelSerializer):
    store_item_name = serializers.CharField(source='store_item_id.name', read_only=True)
    size_name = serializers.CharField(source='size_id.name', read_only=True, allow_null=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'store_item_id', 'store_item_name', 'size_id', 'size_name', 'quantity', 'price_at_order', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_price_at_order(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    account_id = serializers.IntegerField(write_only=True)
    order_items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    store_name = serializers.CharField(source='store_id.name', read_only=True)
    buyer_name = serializers.CharField(source='buyer_id.username', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'account_id', 'store_id', 'store_name', 'buyer_id',
            'buyer_name', 'total_price', 'status', 'notes',
            'order_items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_price', 'order_items', 'created_at', 'updated_at']

    def validate_account_id(self, value):
        try:
            account = Account.objects.get(pk=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist.")
        return value

    def create(self, validated_data):
        validated_data.pop("account_id", None)
        order = Order(**validated_data)
        order.full_clean()
        order.save()
        return order

    def update(self, instance, validated_data):
        validated_data.pop("account_id", None)
        for attr, value in validated_data.items():
            if attr != 'store_id':  # prevent store change
                setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance

class AddOrderItemSerializer(serializers.Serializer):
    """Used to add items to an existing order."""
    store_item_id = serializers.IntegerField()
    size_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)

    def validate_store_item_id(self, value):
        try:
            StoreItem.objects.get(pk=value)
        except StoreItem.DoesNotExist:
            raise serializers.ValidationError("Store item does not exist.")
        return value

    def validate_size_id(self, value):
        if value is not None:
            try:
                StoreItemSize.objects.get(pk=value)
            except StoreItemSize.DoesNotExist:
                raise serializers.ValidationError("Size does not exist.")
        return value