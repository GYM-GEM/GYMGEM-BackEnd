from django.db import models
from django.conf import settings

# Create your models here.


class Profile(models.Model):
    TYPE_CHOICES = [
        ("gym", "Gym"),
        ("trainer", "Trainer"),
        ("store", "Store"),
        ("trainee", "Trainee"),
    ]
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profiles",
        null=True,
    )
    profile_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "profile_type"], name="uniq_account_profiletype"
            )
        ]

    def __str__(self):
        return f"{self.profile_type} Profile for {self.account}"

    @property
    def user(self):
        return self.account
    
    @property
    def get_profile_data(self):
        if self.profile_type == "trainer":
            from trainers.models import Trainer
            return Trainer.objects.get(profile_id=self)
        if self.profile_type == "gym":
            from gyms.models import Gym
            return Gym.objects.get(profile_id=self)
        if self.profile_type == "store":
            from stores.models import Store
            return Store.objects.get(profile_id=self)
        if self.profile_type == "trainee":
            from trainees.models import Trainee
            return Trainee.objects.get(profile_id=self)
        return None