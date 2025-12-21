from datetime import timedelta, datetime, date
from django.utils.timezone import now
from django.db import models
from django.core.exceptions import ValidationError
from profiles.models import Profile
from utils.models import Specialization

# Create your models here.


class Trainer(models.Model):
    profile_id = models.OneToOneField(
        Profile, on_delete=models.CASCADE, primary_key=True
    )
    name = models.CharField(max_length=100)
    profile_picture = models.URLField(
        max_length=500, blank=True, null=True,
        help_text="Link to the trainer's profile picture"
    )
    gender = models.CharField(
        max_length=10, choices=[("male", "Male"), ("female", "Female")], default="male"
    )
    bio = models.TextField(blank=True, null=True,max_length=500)
    birthdate = models.DateField(default=now)
    country = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hourly_rate = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    def __str__(self):
        return f"Trainer<{self.name}> for Profile {self.profile_id}"

    def clean(self):
        if not self.profile_id_id:
            raise ValidationError({"profile_id": "Profile is required."})


    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TrainerSpecialization(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE)
    years_of_experience = models.IntegerField()
    service_location = models.CharField(
        max_length=100,
        choices=[("online", "Online"), ("offline", "Offline"), ("both", "Both")],
    )

    def __str__(self):
        return f"TrainerSpecialization<{self.specialization}> for Trainer {self.trainer.name}"

    def clean(self):
        if self.years_of_experience < 0:
            raise ValidationError(
                {"years_of_experience": "Years of experience cannot be negative."}
            )
        if self.hourly_rate < 0:
            raise ValidationError({"hourly_rate": "Hourly rate cannot be negative."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TrainerExperience(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    work_place = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"TrainerExperience<{self.position} at {self.work_place}> for Trainer {self.trainer.name}"

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                {"end_date": "End date cannot be earlier than start date."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TrainerCalendarSlot(models.Model):
    trainer = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE)
    slot_start_time = models.DateTimeField()
    slot_end_time = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('trainer', 'slot_start_time')
        ordering = ['slot_start_time']

    def clean(self):
        # Ensure a 30-minute gap by preventing overlaps with existing slots for this trainer
        if not self.slot_start_time:
            raise ValidationError({"slot_start_time": "Start time is required."})

        start_dt = self.slot_start_time
        end_dt = (
            self.slot_end_time
            if self.slot_end_time
            else start_dt + timedelta(minutes=30)
        )

        # Check for any overlapping slots for the same trainer
        existing_slots = (
            TrainerCalendarSlot.objects
            .filter(trainer=self.trainer)
            .exclude(pk=self.pk)
        )
        for s in existing_slots:
            s_start = s.slot_start_time
            s_end = s.slot_end_time if s.slot_end_time else s_start + timedelta(minutes=30)
            # Overlap if new_start < existing_end AND new_end > existing_start
            if start_dt < s_end and end_dt > s_start:
                raise ValidationError({
                    "slot_start_time": "Overlaps with an existing slot; a 30-minute gap is required.",
                })

    def save(self, *args, **kwargs):
        # Auto-set end time to 30 minutes after start if not provided
        if self.slot_start_time and not self.slot_end_time:
            self.slot_end_time = self.slot_start_time + timedelta(minutes=30)
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"TrainerCalenderSlot<{self.slot_start_time}> for Trainer {self.trainer.name}"

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
        return f"TrainerRecord<{self.record_date}> for Trainer {self.trainer.name}"
