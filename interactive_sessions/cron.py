from celery import shared_task
from .models import InteractiveSession
from django.utils import timezone
from datetime import timedelta

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60, retry_kwargs={"max_retries": 3})
def handle_unaccepted_sessions(self, *args, **kwargs):
    threshold = timezone.now() - timedelta(days=1)

    sessions = InteractiveSession.objects.filter(
        status='scheduled',
        scheduled_at__slot_start_time__lt=threshold
    ).select_related('trainee')

    for s in sessions:
        s.status = 'refunded'

        if s.trainee and hasattr(s.trainee, "get_profile_data"):
            profile = s.trainee.get_profile_data
            if profile:
                profile.balance += s.fees
                profile.save()

        s.save()



@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60, retry_kwargs={"max_retries": 3})
def expire_requested_sessions(self, *args, **kwargs):
    threshold = timezone.now() - timedelta(hours=1)

    sessions = InteractiveSession.objects.filter(
        status='requested',
        scheduled_at__slot_start_time__lt=threshold
    ).select_related('trainee')

    for s in sessions:
        s.status = 'refunded'

        if s.trainee and hasattr(s.trainee, "get_profile_data"):
            profile = s.trainee.get_profile_data
            if profile:
                profile.balance += s.fees
                profile.save()

        s.save()
