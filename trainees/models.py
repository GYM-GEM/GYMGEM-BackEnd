from django.db import models
from django.core.exceptions import ValidationError
from profiles.models import Profile
# Create your models here.

class Trainee(models.Model):
    profile_id = models.OneToOneField(Profile, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    profile_picture = models.ImageField(upload_to='trainee_profiles/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])
    birthdate = models.DateField()
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Trainee<{self.name}> for Profile {self.profile_id_id}"

    def clean(self):
        if not self.profile_id_id:
            raise ValidationError({'profile_id': 'Profile is required.'})
        if getattr(self.profile_id, 'profile_type', None) != 'trainee':
            raise ValidationError({'profile_id': 'Profile must have profile_type="trainee" to create a Trainee.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class trainee_records(models.Model):
    trainee_id = models.ForeignKey(Trainee, on_delete=models.CASCADE)
    record_date = models.DateField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    height = models.DecimalField(max_digits=5, decimal_places=2)
    body_fat_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    muscle_mass = models.DecimalField(max_digits=5, decimal_places=2)
    bone_mass = models.DecimalField(max_digits=5, decimal_places=2)
    body_water_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    BMR = models.DecimalField(max_digits=7, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TraineeRecord<{self.record_date}> for Trainee {self.trainee_id.name}"