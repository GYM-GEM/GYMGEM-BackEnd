from django.db import models
import uuid
from django.utils import timezone
from utiles.models import Category


# Create your models here.
class Store(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	profile_picture = models.CharField(max_length=255, null=True, blank=True)
	name = models.CharField(max_length=100)
	description = models.CharField(max_length=255, null=True, blank=True)
	TYPE_SUPPLEMENTS = 'supplements'
	TYPE_CLOTHES = 'clothes'
	TYPE_BOTH = 'both'
	STORE_TYPE_CHOICES = [
		(TYPE_SUPPLEMENTS, 'Supplements'),
		(TYPE_CLOTHES, 'Clothes'),
		(TYPE_BOTH, 'Both'),
	]
	store_type = models.CharField(max_length=20, choices=STORE_TYPE_CHOICES)

	class Meta:
		db_table = 'stores'

	def __str__(self) -> str:
		return self.name


class StoreBranch(models.Model):
	id = models.AutoField(primary_key=True)
	store = models.ForeignKey(Store, on_delete=models.CASCADE, db_column='store_id')
	opening_time = models.TimeField(null=True, blank=True)
	closing_time = models.TimeField(null=True, blank=True)
	country = models.CharField(max_length=50, null=True, blank=True)
	state = models.CharField(max_length=50, null=True, blank=True)
	street = models.CharField(max_length=100, null=True, blank=True)
	zip_code = models.CharField(max_length=20, null=True, blank=True)

	class Meta:
		db_table = 'store_branches'

	def __str__(self) -> str:
		return f"{self.store.name} - {self.id}"


class Size(models.Model):
	id = models.SmallAutoField(primary_key=True)
	name = models.CharField(max_length=50)
	description = models.CharField(max_length=255, null=True, blank=True)
	TYPE_CLOTHES = 'clothes'
	TYPE_SHOES = 'shoes'
	TYPE_WEIGHT = 'weight'
	TYPE_VOLUME = 'volume'
	TYPE_CHOICES = [
		(TYPE_CLOTHES, 'Clothes'),
		(TYPE_SHOES, 'Shoes'),
		(TYPE_WEIGHT, 'Weight'),
		(TYPE_VOLUME, 'Volume'),
	]
	type = models.CharField(max_length=10, choices=TYPE_CHOICES)

	class Meta:
		db_table = 'sizes'

	def __str__(self) -> str:
		return self.name


class Item(models.Model):
	id = models.BigAutoField(primary_key=True)
	name = models.CharField(max_length=100)
	description = models.CharField(max_length=255, null=True, blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	stock_quantity = models.IntegerField()
	category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
	brand = models.CharField(max_length=100, null=True, blank=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	size = models.ForeignKey(Size, null=True, blank=True, on_delete=models.SET_NULL, db_column='size_id')
	expiry_date = models.DateField(null=True, blank=True)
	store = models.ForeignKey(Store, null=True, blank=True, on_delete=models.SET_NULL, db_column='store_id')
	branch = models.ForeignKey(StoreBranch, null=True, blank=True, on_delete=models.SET_NULL, db_column='branch_id')

	class Meta:
		db_table = 'items'

	def __str__(self) -> str:
		return self.name


# Create your models here.
