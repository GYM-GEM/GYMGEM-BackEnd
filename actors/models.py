from django.db import models
from django.utils import timezone
from utiles.models import Status
# Create your models here.
class Actor(models.Model):
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, null=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.ForeignKey(Status, null=True, blank=True, on_delete=models.SET_NULL)
    last_seen = models.DateTimeField(null=True, blank=True)
    default_profile = models.UUIDField(null=True, blank=True )

    class Meta:
        db_table = 'actors'

    def __str__(self) -> str:
        return self.username
