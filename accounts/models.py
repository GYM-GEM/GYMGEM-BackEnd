from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Account(User):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    default_profile = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)