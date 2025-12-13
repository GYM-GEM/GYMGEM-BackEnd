from django.db import models
from django.core.exceptions import ValidationError
from profiles.models import Profile
from accounts.models import Account
# Create your models here.

class Store(models.Model):
    profile_id = models.OneToOneField(Profile, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='store_profiles/', blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    store_type = models.CharField(max_length=100, choices=[('supplements', 'Supplements'), ('clothes', 'Clothes'), ('both', 'Both')], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Store<{self.name}> for Profile {self.profile_id_id}"

    def clean(self):
        """Only allow creating a Store for profiles of type 'store'."""
        # Ensure a profile is set and is of the correct type
        if not self.profile_id_id:
            raise ValidationError({
                'profile_id': 'Profile is required.'
            })
        if getattr(self.profile_id, 'profile_type', None) != 'store':
            raise ValidationError({
                'profile_id': 'Profile must have profile_type="store" to create a Store.'
            })

    def save(self, *args, **kwargs):
        # Enforce validation at the model layer, even when not using serializers/forms
        self.full_clean()
        return super().save(*args, **kwargs)

class StoreBranch(models.Model):
    store_id = models.ForeignKey(Store, on_delete=models.CASCADE)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    country = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"StoreBranch<{self.branch_name}> of Store {self.store.name}"
    
    def clean(self):
        """Validate StoreBranch fields."""
        if self.opening_time >= self.closing_time:
            raise ValidationError({
                'closing_time': 'Closing time must be after opening time.'
            })    
    def save(self, *args, **kwargs):
        # Enforce validation at the model layer, even when not using serializers/forms
        self.full_clean()
        return super().save(*args, **kwargs)

class StoreItemSize(models.Model):
    name=models.CharField(max_length=100)
    type=models.CharField(max_length=100)
    description=models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"StoreItemSize<{self.size}> for Item {self.store_item_id.name}"
    def clean(self):
        """Validate StoreItemSize fields."""
        if not self.name:
            raise ValidationError({
                'name': 'Size name is required.'
            })
    def save(self, *args, **kwargs):
        # Enforce validation at the model layer, even when not using serializers/forms
        self.full_clean()
        return super().save(*args, **kwargs)
    
class StoreItem(models.Model):
    store_id = models.ForeignKey(Store, on_delete=models.CASCADE)
    branch_id = models.ForeignKey(StoreBranch, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, choices=[('supplements', 'Supplements'), ('clothes', 'Clothes'),('foods', 'Foods')], blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    def get_total_quantity(self):
        """Calculate total quantity across all sizes."""
        inventories = StoreItemInventory.objects.filter(store_item_id=self)
        total_quantity = sum(inventory.quantity for inventory in inventories)
        return total_quantity
     
    def __str__(self):
        return f"StoreItem<{self.name}> of Store {self.store_id.name}"  
    def clean(self):
        """Validate StoreItem fields."""
        if self.expiration_date and self.expiration_date <= models.DateField().to_python('today'):
            raise ValidationError({
                'expiration_date': 'Expiration date must be in the future.'
            })
    def save(self, *args, **kwargs):
        # Enforce validation at the model layer, even when not using serializers/forms
        self.full_clean()
        return super().save(*args, **kwargs)

class StoreItemInventory(models.Model):
    store_item_id = models.ForeignKey(StoreItem, on_delete=models.CASCADE)
    size_id = models.ForeignKey(StoreItemSize, on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"StoreItemInventory<{self.store_item_id.name} - {self.size_id.name if self.size_id else 'No Size'}>"
    
    def clean(self):
        """Validate StoreItemInventory fields."""
        if self.quantity < 0:
            raise ValidationError({
                'quantity': 'Quantity cannot be negative.'
            })
    def save(self, *args, **kwargs):
        # Enforce validation at the model layer, even when not using serializers/forms
        self.full_clean()
        return super().save(*args, **kwargs)
      
class Order(models.Model):    
    store_id = models.ForeignKey(Store, on_delete=models.CASCADE)
    buyer_id = models.ForeignKey(Account, on_delete=models.CASCADE)  # who ordered
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices= [('pending', 'Pending'), ('confirmed', 'Confirmed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending')
    notes = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order<{self.id}> from {self.store_id.name} by {self.buyer_id.username}"

    def calculate_total(self):
        """Recalculate total from order items."""
        total = sum(item.price_at_order * item.quantity for item in self.orderitem_set.all())
        self.total_price = total
        self.save()
        return total  
     
    def clean(self):
        if self.total_price < 0:
            raise ValidationError({'total_price': 'Total price cannot be negative.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class OrderItem(models.Model):
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    store_item_id = models.ForeignKey(StoreItem, on_delete=models.CASCADE)
    size_id = models.ForeignKey(StoreItemSize, on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.PositiveIntegerField()
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OrderItem<{self.store_item_id.name}>"
    def clean(self):
        """Validate OrderItem fields."""
        if self.quantity <= 0:
            raise ValidationError({
                'quantity': 'Quantity must be greater than zero.'
            })
        if self.price_at_order <= 0:
            raise ValidationError({
                'price_at_order': 'Price at order must be greater than zero.'
            })
    def save(self, *args, **kwargs):
        # Enforce validation at the model layer, even when not using serializers/forms
        self.full_clean()
        return super().save(*args, **kwargs)    
    
class InventoryLog(models.Model):
    store_item_id = models.ForeignKey(StoreItemInventory, on_delete=models.CASCADE)
    change_type = models.CharField(max_length=20, choices=[
        ('add', 'Added'),
        ('remove', 'Removed'),
        ('order', 'Ordered'),
        ('adjustment', 'Adjustment'),
    ])
    quantity_changed = models.IntegerField()  
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"InventoryLog: {self.store_item_id.name} {self.change_type} ({self.quantity_changed})"