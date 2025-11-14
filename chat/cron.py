from celery import shared_task
from .models import Message
from django.utils import timezone
from datetime import timedelta

@shared_task
def delete_old_messages():
    threshold = timezone.now() - timedelta(days=7)
    Message.objects.filter(is_deleted=True, edited_at__lt=threshold).delete()
