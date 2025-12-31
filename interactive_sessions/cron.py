from celery import shared_task
from .models import InteractiveSession
from django.utils import timezone
from datetime import timedelta

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def handle_unaccepted_sessions(self):
    threshold = timezone.now() - timedelta(days=1)

    sessions = InteractiveSession.objects.filter(
        status='scheduled',
        scheduled_at__slot_start_time__lt=threshold,
        financials_applied=False
    ).select_related('trainee')

    for session in sessions:
        session.status = 'refunded'
        session.refund_trainee()


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def expire_requested_sessions():
    threshold = timezone.now() - timedelta(hours=1)

    sessions = InteractiveSession.objects.filter(
        status='requested',
        scheduled_at__slot_start_time__lt=threshold,
        financials_applied=False
    )

    for session in sessions:
        session.status = 'refunded'
        session.refund_trainee()