from django.db import models
from django.contrib.auth.models import AbstractUser

class Account(AbstractUser):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("suspended", "Suspended"),
    ]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    default_profile = models.ForeignKey(
        "profiles.Profile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="default_for_accounts",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True, default="active")
    admin_deleted = models.BooleanField(default=False)
    def __str__(self):
        return self.username
    
