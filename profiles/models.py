from django.db import models
from accounts.models import Account

# Create your models here.

class Profile(models.Model):
    TYPE_CHOICES = [
        ('gym', 'Gym'),
        ('trainer', 'Trainer'),
        ('store', 'Store'),
        ('trainee', 'Trainee'),
    ]
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='profiles')
    profile_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    
