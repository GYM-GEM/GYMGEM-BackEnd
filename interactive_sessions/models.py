from django.db import models
from django.core.validators import MinValueValidator
from django.db import transaction
# Create your models here.
class InteractiveSession(models.Model):
    session_title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_at = models.ForeignKey('trainers.TrainerCalendarSlot', on_delete=models.CASCADE, related_name='interactive_sessions')
    trainer = models.ForeignKey('profiles.Profile', related_name='interactive_sessions_trainer', blank=True, null=True, on_delete=models.CASCADE)
    trainee = models.ForeignKey('profiles.Profile', related_name='interactive_sessions_trainee', blank=True, null=True, on_delete=models.CASCADE)
    fees = models.IntegerField(default=50, validators=[MinValueValidator(50)])
    
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    
    total_active_minutes = models.IntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=[
        ('requested', 'Requested'),  #at first when session is requested from the trainee
        ('scheduled', 'Scheduled'), #when the payment is done and session is scheduled
        ('completed', 'Completed'), #when the session is done
        ('canceled', 'Canceled'),   #when the session is canceled by trainee after the allowed time
        ('aborted', 'Aborted'),     #when the session is aborted by trainer due to some reason
        ('refunded', 'Refunded'),   #when the payment is refunded to the trainee due to cancellation in a good timing or abortion by trainer
        ('rejected', 'Rejected'),    #when the session is rejected by the trainer
        ('live', 'Live'),           #when the session is currently live
        ('waiting', 'Waiting for Trainee'), #when the trainer is waiting for the trainee to join
        ('no_show', 'No Show')    #when the trainee does not show up for the session
    ], default='requested')
    
    is_completed = models.BooleanField(default=False)
    # Marker to ensure financials (trainer payouts / refunds) are applied once
    financials_applied = models.BooleanField(default=False)
    
    def __str__(self):
        return f"InteractiveSession<{self.session_title}> scheduled at {self.scheduled_at}"
    
    # InteractiveSession model


    def refund_trainee(self):
        if self.financials_applied:
            return

        trainee_data = self.trainee.get_profile_data
        if not trainee_data:
            return

        with transaction.atomic():
            trainee_data.balance += self.fees
            trainee_data.save(update_fields=["balance"])

            self.financials_applied = True
            self.status = "refunded"
            self.save(update_fields=["financials_applied", "status"])
