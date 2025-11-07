from django.db import models
from django.contrib.auth.models import AbstractUser

class Account(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    default_profile = models.ForeignKey(
        "profiles.Profile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="default_for_accounts",
    )
    status = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.username
    
