from rest_framework import serializers
from accounts.models import Account
from .models import Store, StoreBranch, StoreItem,StoreItemInventory, StoreItemSize, Order, OrderItem, InventoryLog
from profiles.models import Profile
from utils.views import  get_profile_id_from_token
from django.db import transaction

class StoreSerializer(serializers.ModelSerializer):
    profile_id = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Store
        fields = ['id', 'profile_id', 'name', 'profile_picture','description','store_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'profile_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Get profile_id from token
        profile_id = get_profile_id_from_token(self.context.get("request"))
        
        if not profile_id:
            raise serializers.ValidationError("Profile ID not found in token.")
        
        # Get the profile and verify it's a store profile
        try:
            profile = Profile.objects.get(pk=profile_id)
        except Profile.DoesNotExist:
            raise serializers.ValidationError("Profile does not exist.")
        
        if profile.profile_type != "store":
            raise serializers.ValidationError("Profile must be of type 'store'.")
        
        # Check if store already exists for this profile
        if Store.objects.filter(profile_id=profile).exists():
            raise serializers.ValidationError("Store already exists for this profile.")
        
        # Create store with the profile
        store = Store(profile_id=profile, **validated_data)
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
    
    class Meta:
        model = StoreBranch
        fields = ['id', 'store_id', 'opening_time', 'closing_time', 'country', 'state', 'street', 'zip_code', 'created_at', 'updated_at']
        read_only_fields = ['id', 'store_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Get profile_id from token
        profile_id = get_profile_id_from_token(self.context.get("request"))
        
        if not profile_id:
            raise serializers.ValidationError("Profile ID not found in token.")
        
        # Get the store for this profile
        try:
            store = Store.objects.get(profile_id=profile_id)
        except Store.DoesNotExist:
            raise serializers.ValidationError("Store does not exist for this profile.")
        
        # Set store_id
        validated_data['store_id'] = store
        
        store_branch = StoreBranch(**validated_data)
        store_branch.full_clean()
        store_branch.save()
        return store_branch

    def update(self, instance, validated_data):
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
        read_only_fields = ['id', 'store_item_id', 'created_at', 'updated_at']

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value
    
    def validate_size_id(self, value):
        if not value:
            raise serializers.ValidationError("Size is required.")
        try:
            StoreItemSize.objects.get(pk=value.id if hasattr(value, 'id') else value)
        except StoreItemSize.DoesNotExist:
            raise serializers.ValidationError("Size does not exist.")
        return value

class InventoryLogSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='store_item_id.store_item_id.name', read_only=True)
 
    class Meta:
        model = InventoryLog
        fields = [
            'id', 'store_item_id', 'item_name', 'change_type',
            'quantity_changed', 'reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class StoreItemSerializer(serializers.ModelSerializer):
    inventory = StoreItemInventorySerializer(source='storeiteminventory_set', many=True, required=False, allow_null=True)
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = StoreItem
        fields = [
            'id', 'store_id', 'branch_id', 'name', 'description',
            'price', 'category', 'brand', 'expiration_date',
            'inventory', 'total_quantity', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'store_id', 'created_at', 'updated_at', 'total_quantity']

    def get_total_quantity(self, obj):
        return obj.get_total_quantity()

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def create(self, validated_data):
        # Get profile_id from token
        profile_id = get_profile_id_from_token(self.context.get("request"))
        
        if not profile_id:
            raise serializers.ValidationError("Profile ID not found in token.")
        
        # Get the store for this profile
        try:
            store = Store.objects.get(profile_id=profile_id)
        except Store.DoesNotExist:
            raise serializers.ValidationError("Store does not exist for this profile.")
        
        # Set store_id
        validated_data['store_id'] = store

        # Validate branch_id if provided
        branch_id = validated_data.get('branch_id')
        if branch_id and branch_id.store_id != store:
            raise serializers.ValidationError("Branch must belong to the authenticated user's store.")

        # Extract inventory data before creating the item
        inventory_data = validated_data.pop('storeiteminventory_set', [])
        
        # Create the item
        with transaction.atomic():
            item = StoreItem.objects.create(**validated_data)

            for inv_data in inventory_data:
                # size_id is ALREADY the StoreItemSize object here
                size_obj = inv_data.get('size_id')
                quantity = inv_data.get('quantity')

                # No need to call .objects.get()! DRF did it for you.
                StoreItemInventory.objects.create(
                    store_item_id=item,
                    size_id=size_obj, 
                    quantity=quantity
                )

        return item
        
    def update(self, instance, validated_data):
        # Extract inventory data if provided
        inventory_data = validated_data.pop('storeiteminventory_set', None)
        
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if inventory_data is not None:
                instance.storeiteminventory_set.all().delete()
                for inv_data in inventory_data:
                    # Again, use the object directly
                    size_obj = inv_data.get('size_id')
                    quantity = inv_data.get('quantity')
                    
                    StoreItemInventory.objects.create(
                        store_item_id=instance,
                        size_id=size_obj,
                        quantity=quantity
                    )
        
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
    order_items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    store_name = serializers.CharField(source='store_id.name', read_only=True)
    buyer_name = serializers.CharField(source='buyer_id.username', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'store_id', 'store_name', 'buyer_id',
            'buyer_name', 'total_price', 'status', 'notes',
            'order_items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'buyer_id', 'total_price', 'order_items', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Get buyer_id from context if not provided
        buyer_id = self.context.get('request').data.get('buyer_id')
        if not buyer_id:
            # Get account ID from JWT token
            auth_header = self.context.get('request').headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token_string = auth_header.split(' ')[1]
                from rest_framework_simplejwt.tokens import AccessToken
                try:
                    access_token = AccessToken(token_string)
                    account_id = access_token['user_id']
                    buyer = Account.objects.get(pk=account_id)
                    validated_data['buyer_id'] = buyer
                except Exception:
                    raise serializers.ValidationError("Invalid token or account not found.")
            else:
                raise serializers.ValidationError("Authorization required.")
        
        order = Order(**validated_data)
        order.full_clean()
        order.save()
        return order

    def update(self, instance, validated_data):
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
    
