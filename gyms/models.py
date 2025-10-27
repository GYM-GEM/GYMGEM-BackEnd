from django.db import models
from accounts.models import Account
from profiles.models import Profile
# Create your models here.

class Gym(models.Model):
    profile_id = models.ForeignKey(Profile, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

