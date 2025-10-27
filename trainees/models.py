from django.db import models
from profiles.models import Profile
# Create your models here.

class Trainee(models.Model):
    profile_id = models.ForeignKey(Profile, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
