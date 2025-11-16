from django.db import models

# Create your models here.
class InteractiveSession(models.Model):
    session_title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_at = models.ForeignKey('trainers.TrainerCalendarSlot', on_delete=models.CASCADE, related_name='interactive_sessions')
    participants = models.ManyToManyField('profiles.Profile', related_name='interactive_sessions', blank=True)
    
    def __str__(self):
        return f"InteractiveSession<{self.session_title}> scheduled at {self.scheduled_at}"