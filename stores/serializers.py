from rest_framework import serializers
from .models import (
    Store,
    StoreBranch,
    StoreItem,
    StoreItemInventory,
    StoreItemSize,
    Order,
    OrderItem,
    InventoryLog,
)
from profiles.models import Profile
from utils.views import get_profile_id_from_token
from django.db import transaction


class StoreBranchSerializer(serializers.ModelSerializer):
    profile_id = serializers.SerializerMethodField()

    class Meta:
        model = StoreBranch
        fields = [
            "id",
            "store_id",
            "profile_id",
            "opening_time",
            "closing_time",
            "country",
            "state",
            "street",
            "zip_code",
            "created_at",
            "updated_at",
            "phone_number",
        ]
        read_only_fields = ["id", "store_id", "profile_id", "created_at", "updated_at"]

    def get_profile_id(self, obj):
        return obj.store_id.profile_id.id

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
        validated_data["store_id"] = store

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


class StoreSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="profile_id.id", read_only=True)
    branches = StoreBranchSerializer(
        source="storebranch_set", many=True, read_only=True
    )

    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "profile_picture",
            "description",
            "store_type",
            "branches",
            "created_at",
            "updated_at",
            "phone_number",
        ]
        read_only_fields = ["id", "branches", "created_at", "updated_at"]

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


class StoreItemSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreItemSize
        fields = ["id", "name", "created_at"]
        read_only_fields = ["created_at"]


class StoreItemInventorySerializer(serializers.ModelSerializer):
    size_name = serializers.CharField(source="size_id.name", read_only=True)

    class Meta:
        model = StoreItemInventory
        fields = [
            "id",
            "store_item_id",
            "size_id",
            "size_name",
            "quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "store_item_id", "created_at", "updated_at"]

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value

    def validate_size_id(self, value):
        if not value:
            raise serializers.ValidationError("Size is required.")
        try:
            StoreItemSize.objects.get(pk=value.id if hasattr(value, "id") else value)
        except StoreItemSize.DoesNotExist:
            raise serializers.ValidationError("Size does not exist.")
        return value


class InventoryLogSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(
        source="store_item_id.store_item_id.name", read_only=True
    )

    class Meta:
        model = InventoryLog
        fields = [
            "id",
            "store_item_id",
            "item_name",
            "change_type",
            "quantity_changed",
            "reason",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class StoreItemSerializer(serializers.ModelSerializer):
    inventory = StoreItemInventorySerializer(
        source="storeiteminventory_set", many=True, required=False, allow_null=True
    )
    total_quantity = serializers.SerializerMethodField()
    profile_id = serializers.SerializerMethodField()

    class Meta:
        model = StoreItem
        fields = [
            "id",
            "store_id",
            "profile_id",
            "branch_id",
            "name",
            "description",
            "item_image",
            "price",
            "category",
            "status",
            "brand",
            "expiration_date",
            "inventory",
            "total_quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "store_id",
            "profile_id",
            "created_at",
            "updated_at",
            "total_quantity",
        ]

    def get_total_quantity(self, obj):
        return obj.get_total_quantity()

    def get_profile_id(self, obj):
        return obj.store_id.profile_id.id

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
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
        validated_data["store_id"] = store

        # Validate branch_id if provided
        branch_id = validated_data.get("branch_id")
        if branch_id and branch_id.store_id != store:
            raise serializers.ValidationError(
                "Branch must belong to the authenticated user's store."
            )

        # Extract inventory data before creating the item
        inventory_data = validated_data.pop("storeiteminventory_set", [])

        # Create the item
        with transaction.atomic():
            item = StoreItem.objects.create(**validated_data)

            for inv_data in inventory_data:
                # size_id is ALREADY the StoreItemSize object here
                size_obj = inv_data.get("size_id")
                quantity = inv_data.get("quantity")

                # No need to call .objects.get()! DRF did it for you.
                StoreItemInventory.objects.create(
                    store_item_id=item, size_id=size_obj, quantity=quantity
                )

        return item

    def update(self, instance, validated_data):
        # Extract inventory data if provided
        inventory_data = validated_data.pop("storeiteminventory_set", None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if inventory_data is not None:
                instance.storeiteminventory_set.all().delete()
                for inv_data in inventory_data:
                    # Again, use the object directly
                    size_obj = inv_data.get("size_id")
                    quantity = inv_data.get("quantity")

                    StoreItemInventory.objects.create(
                        store_item_id=instance, size_id=size_obj, quantity=quantity
                    )

        return instance


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items within an order."""

    store_item_id = serializers.IntegerField()
    size_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)

    def validate_store_item_id(self, value):
        try:
            item = StoreItem.objects.get(pk=value)
            # Check if item has sufficient inventory
            if item.get_total_quantity() <= 0:
                raise serializers.ValidationError("Item is out of stock.")
            return value
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

    def validate(self, data):
        store_item_id = data.get("store_item_id")
        size_id = data.get("size_id")
        quantity = data.get("quantity")

        # Check inventory for specific size if size is specified
        if size_id:
            try:
                inventory = StoreItemInventory.objects.get(
                    store_item_id=store_item_id, size_id=size_id
                )
                if inventory.quantity < quantity:
                    raise serializers.ValidationError(
                        f"Insufficient inventory for size. Available: {inventory.quantity}"
                    )
            except StoreItemInventory.DoesNotExist:
                raise serializers.ValidationError("Size not available for this item.")
        else:
            # Check total inventory across all sizes
            try:
                item = StoreItem.objects.get(pk=store_item_id)
                if item.get_total_quantity() < quantity:
                    raise serializers.ValidationError(
                        f"Insufficient inventory. Available: {item.get_total_quantity()}"
                    )
            except StoreItem.DoesNotExist:
                pass  # Already validated above

        return data


class OrderItemSerializer(serializers.ModelSerializer):
    store_item_name = serializers.CharField(source="store_item_id.name", read_only=True)
    size_name = serializers.CharField(
        source="size_id.name", read_only=True, allow_null=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "store_item_id",
            "store_item_name",
            "size_id",
            "size_name",
            "quantity",
            "price_at_order",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_price_at_order(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(source="orderitem_set", many=True, read_only=True)
    store_name = serializers.CharField(source="store_id.name", read_only=True)
    buyer_name = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    profile_id = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "profile_id",
            "store_name",
            "buyer_id",
            "buyer_name",
            "total_price",
            "status",
            "notes",
            "order_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "profile_id",
            "buyer_id",
            "total_price",
            "order_items",
            "created_at",
            "updated_at",
        ]

    def get_total_price(self, obj):
        """Return total price in gems (1 USD = 10 gems)"""
        return int(obj.total_price * 10)

    def get_profile_id(self, obj):
        return obj.store_id.profile_id.id

    def get_buyer_name(self, obj):
        """Get buyer name from profile's account or trainee name"""
        if obj.buyer_id:
            # Try to get name from trainee profile data
            profile_data = obj.buyer_id.get_profile_data
            if profile_data and hasattr(profile_data, 'name'):
                return profile_data.name
            # Fallback to account username
            if obj.buyer_id.account:
                return obj.buyer_id.account.username
        return None

    def create(self, validated_data):
        # Extract order items data from raw request data
        request = self.context.get("request")
        order_items_data = request.data.get("order_items_data", [])
        
        # Fallback to 'order_items' if 'order_items_data' is not provided
        if not order_items_data:
            order_items_data = request.data.get("order_items", [])

        # Get profile_id from request data
        profile_id = request.data.get("profile_id")
        if not profile_id:
            raise serializers.ValidationError("profile_id is required.")

        # Find the store
        try:
            store = Store.objects.get(profile_id=profile_id)
        except Store.DoesNotExist:
            raise serializers.ValidationError("Store not found for this profile_id.")

        validated_data["store_id"] = store

        # Get buyer_id from context if not provided (buyer_id is optional)
        buyer_id = get_profile_id_from_token(request)
        if buyer_id:
            try:
                buyer = Profile.objects.get(pk=buyer_id)
                validated_data["buyer_id"] = buyer
            except Profile.DoesNotExist:
                validated_data["buyer_id"] = None
        else:
            # Try to get account ID from JWT token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token_string = auth_header.split(" ")[1]
                from rest_framework_simplejwt.tokens import AccessToken

                try:
                    access_token = AccessToken(token_string)
                    account_id = access_token["user_id"]
                    buyer = Profile.objects.get(pk=account_id)
                    validated_data["buyer_id"] = buyer
                except Exception:
                    validated_data["buyer_id"] = None
            else:
                validated_data["buyer_id"] = None

        # Calculate total order price before creating the order
        total_order_price = 0
        for item_data in order_items_data:
            if isinstance(item_data, dict):
                store_item_id = item_data.get("store_item_id")
                quantity = item_data.get("quantity", 0)
                if store_item_id and quantity:
                    try:
                        store_item = StoreItem.objects.get(pk=store_item_id)
                        # Price is in cents, convert to gems (1 USD = 10 gems, so cents / 10)
                        item_price_gems = store_item.price // 10
                        total_order_price += item_price_gems * quantity
                    except StoreItem.DoesNotExist:
                        pass  # Will be caught during order item creation

        # Check if buyer has sufficient balance
        buyer = validated_data.get("buyer_id")
        if buyer:
            try:
                buyer_balance = buyer.get_profile_data
                if buyer_balance.balance < total_order_price:
                    raise serializers.ValidationError(
                        f"Insufficient balance. Required: {total_order_price} gems, Available: {buyer_balance.balance} gems."
                    )
            except Exception:
                raise serializers.ValidationError("Unable to retrieve buyer balance.")

        # Create order with transaction to ensure data consistency
        try:
            with transaction.atomic():
                order = Order(**validated_data)
                order.full_clean()
                order.save()
                # Create order items if provided
                for item_data in order_items_data:
                    # Basic validation
                    if not isinstance(item_data, dict):
                        raise serializers.ValidationError("Invalid order item data format.")
                    
                    try:
                        store_item_id = item_data.get("store_item_id")
                        quantity = item_data.get("quantity")
                        size_id = item_data.get("size_id")
                    except Exception:
                        raise serializers.ValidationError("Invalid order item data format.")
                    
                    if not store_item_id or not quantity:
                        raise serializers.ValidationError("store_item_id and quantity are required for each order item.")
                    
                    if quantity <= 0:
                        raise serializers.ValidationError("Quantity must be greater than zero.")
                    
                    store_item = StoreItem.objects.get(pk=store_item_id)

                    # Get current price
                    price_at_order = (
                        store_item.price / 100.0
                    )  # Convert from cents to dollars

                    # Create order item
                    OrderItem.objects.create(
                        order_id=order,
                        store_item_id=store_item,
                        size_id=size_id,
                        quantity=quantity,
                        price_at_order=price_at_order,
                    )

                    # Update inventory
                    if size_id:
                        # Specific size inventory
                        inventory = StoreItemInventory.objects.get(
                            store_item_id=store_item, size_id=size_id
                        )
                        if inventory.quantity < quantity:
                            raise serializers.ValidationError(
                                f"Insufficient inventory for item {store_item.name}, size {size_id}. Available: {inventory.quantity}"
                            )
                        inventory.quantity -= quantity
                        inventory.save()
                    else:
                        # Reduce from available inventory
                        inventories = StoreItemInventory.objects.filter(
                            store_item_id=store_item
                        ).order_by("quantity")

                        remaining_quantity = quantity
                        for inventory in inventories:
                            if remaining_quantity <= 0:
                                break
                            if inventory.quantity > 0:
                                deduct = min(inventory.quantity, remaining_quantity)
                                inventory.quantity -= deduct
                                inventory.save()
                                remaining_quantity -= deduct
                        
                        if remaining_quantity > 0:
                            raise serializers.ValidationError(
                                f"Insufficient inventory for item {store_item.name}. Available: {store_item.get_total_quantity()}"
                            )
                
                # Calculate total price
                order.calculate_total()
                
                buyer_balance = buyer.get_profile_data
                buyer_balance.balance -= total_order_price
                buyer_balance.save()
                    
        except Exception as e:
            raise serializers.ValidationError(str(e))

            

        return order

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr != "store_id":  # prevent store change
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
