"""
Celery tasks for chat message cleanup.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import Message


logger = logging.getLogger('gymgem.celery')


@shared_task
def delete_old_messages() -> str:
    """
    Delete messages that have been soft-deleted for more than 7 days.
    
    This task cleans up old deleted messages to free up database space.
    """
    threshold = timezone.now() - timedelta(days=7)
    
    # Get count before deletion for logging
    messages_to_delete = Message.objects.filter(
        is_deleted=True,
        edited_at__lt=threshold
    )
    count = messages_to_delete.count()
    
    if count > 0:
        messages_to_delete.delete()
        logger.info(
            "Deleted %d old messages (deleted more than 7 days ago)",
            count
        )
    else:
        logger.debug("No old messages to delete")
    
    return f"Deleted {count} old messages"
