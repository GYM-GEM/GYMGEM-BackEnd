from django.db import models
from django.core.exceptions import ValidationError
from profiles.models import Profile
# Create your models here.

class Gym(models.Model):
    profile_id = models.OneToOneField(Profile, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Gym<{self.name}> for Profile {self.profile_id_id}"

    def clean(self):
        if not self.profile_id_id:
            raise ValidationError({'profile_id': 'Profile is required.'})
        if getattr(self.profile_id, 'profile_type', None) != 'gym':
            raise ValidationError({'profile_id': 'Profile must have profile_type="gym" to create a Gym.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
    
class Gym_branch(models.Model):
    gym_id = models.ForeignKey(Gym, on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    state=models.CharField(max_length=100)
    street=models.CharField(max_length=100)
    zip_code=models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GymBranch<{self.branch_name}> of Gym {self.gym.name}"

class gym_slots(models.Model):
    gym_id = models.ForeignKey(Gym, on_delete=models.CASCADE)
    branch_id = models.ForeignKey(Gym_branch, on_delete=models.CASCADE)
    slot_start_time = models.TimeField()
    slot_end_time = models.TimeField()
    TYPE_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('mix', 'Mix'),
    ]
    gender = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GymSlot<{self.slot_start_time} - {self.slot_end_time}> for Branch {self.branch_id.branch_name}"
