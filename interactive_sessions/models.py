from django.db import models

# Create your models here.
class InteractiveSession(models.Model):
    session_title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_at = models.ForeignKey('trainers.TrainerCalendarSlot', on_delete=models.CASCADE, related_name='interactive_sessions')
    trainer = models.ManyToManyField('profiles.Profile', related_name='interactive_sessions', blank=True)
    trainee = models.ManyToManyField('profiles.Profile', related_name='interactive_sessions_second', blank=True)
    status = models.CharField(max_length=20, choices=[
        ('requested', 'Requested'),  #at first when session is requested from the trainee
        ('pending', 'Pending'),     #when the trainer confirm the session and waiting for payment
        ('scheduled', 'Scheduled'), #when the payment is done and session is scheduled
        ('completed', 'Completed'), #when the session is done
        ('canceled', 'Canceled'),   #when the session is canceled by trainee after the 
        ('aborted', 'Aborted'),     #when the session is aborted by trainer due to some reason
        ('refunded', 'Refunded'),   #when the payment is refunded to the trainee due to cancellation in a good timing or abortion by trainer
        ('rejected', 'Rejected')    #when the session is rejected by the trainer
    ], default='requested')
    
    def __str__(self):
        return f"InteractiveSession<{self.session_title}> scheduled at {self.scheduled_at}"