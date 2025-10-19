from django.db import models
import uuid
from django.utils import timezone


# Create your models here.
class TrainerProfile(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	profile_picture = models.CharField(max_length=255, null=True, blank=True)
	birthdate = models.DateField(null=True, blank=True)
	GENDER_M = 'm'
	GENDER_F = 'f'
	GENDER_CHOICES = [
		(GENDER_M, 'Male'),
		(GENDER_F, 'Female'),
	]
	gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
	balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	country = models.CharField(max_length=50, null=True, blank=True)
	state = models.CharField(max_length=50, null=True, blank=True)
	zip_code = models.CharField(max_length=20, null=True, blank=True)

	class Meta:
		db_table = 'trainers'

	def __str__(self) -> str:
		return str(self.id)


# Create your models here.
