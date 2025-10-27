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
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['account', 'profile_type'], name='uniq_account_profiletype'
            )
        ]
    
    def __str__(self):
        return f"{self.profile_type} Profile for {self.account.username}"
