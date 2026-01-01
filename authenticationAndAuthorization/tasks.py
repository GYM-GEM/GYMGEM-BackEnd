"""
Celery tasks for authentication and authorization.
"""
import logging

from celery import shared_task
from django.core.management import call_command


logger = logging.getLogger('gymgem.celery')


@shared_task
def flush_expired_tokens() -> str:
    """
    Flush expired JWT tokens from the database.
    
    Calls Django's flushexpiredtokens management command.
    """
    logger.info("Starting flush_expired_tokens task")
    
    try:
        call_command('flushexpiredtokens')
        logger.info("Expired tokens flushed successfully")
        return "Expired tokens flushed successfully"
    except Exception as e:
        logger.error("Failed to flush expired tokens: %s", str(e))
        raise
