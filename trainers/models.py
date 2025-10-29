from django.db import models
from django.core.exceptions import ValidationError
from profiles.models import Profile
from utils.models import Specialization
# Create your models here.

class Trainer(models.Model):
    profile_id = models.OneToOneField(Profile, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    profile_picture = models.ImageField(upload_to='trainee_profiles/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])
    birthdate = models.DateField()
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Trainer<{self.name}> for Profile {self.profile_id_id}"

    def clean(self):
        if not self.profile_id_id:
            raise ValidationError({'profile_id': 'Profile is required.'})
        if getattr(self.profile_id, 'profile_type', None) != 'trainer':
            raise ValidationError({'profile_id': 'Profile must have profile_type="trainer" to create a Trainer.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TrainerSpecialization(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE)
    years_of_experience = models.IntegerField()
    hourly_rate = models.DecimalField(max_digits=7, decimal_places=2)
    service_location = models.CharField(max_length=100, choices=[("online", "Online"), ("offline", "Offline"), ("both", "Both")])

    def __str__(self):
        return f"TrainerSpecialization<{self.specialization}> for Trainer {self.trainer.name}"


class TrainerExperience(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    work_place = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"TrainerExperience<{self.position} at {self.work_place}> for Trainer {self.trainer.name}"
    

class TrainerCalendarSlot(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    slot_date = models.DateField()
    slot_start_time = models.TimeField()
    slot_end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TrainerCalenderSlot<{self.slot_date} {self.slot_start_time}-{self.slot_end_time}> for Trainer {self.trainer_id.name}"
    
class TrainerRecord(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
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
        return f"TrainerRecord<{self.record_date}> for Trainer {self.trainer_id.name}"