from django.db import models
from django.core.exceptions import ValidationError
from profiles.models import Profile
# Create your models here.

class Store(models.Model):
    profile_id = models.OneToOneField(Profile, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
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