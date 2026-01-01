"""
Celery tasks for interactive session management.
"""
import logging
from datetime import timedelta
from typing import List

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import InteractiveSession


logger = logging.getLogger('gymgem.celery')


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3}
)
def handle_unaccepted_sessions(self, *args, **kwargs) -> str:
    """
    Handle sessions that were scheduled but never started.
    
    Refunds the trainee for sessions that passed the threshold
    without being accepted/started.
    """
    threshold = timezone.now() - timedelta(days=1)

    sessions = InteractiveSession.objects.filter(
        status='scheduled',
        scheduled_at__slot_start_time__lt=threshold
    ).select_related('trainee')

    refunded_count = 0
    
    for session in sessions:
        try:
            with transaction.atomic():
                session.status = 'refunded'

                if session.trainee and hasattr(session.trainee, "get_profile_data"):
                    profile = session.trainee.get_profile_data
                    if profile:
                        old_balance = profile.balance
                        profile.balance += session.fees
                        profile.save(update_fields=["balance"])
                        
                        logger.info(
                            "Refunded session %s: trainee=%s, fees=%s, balance: %s -> %s",
                            session.id,
                            session.trainee.id,
                            session.fees,
                            old_balance,
                            profile.balance
                        )

                session.save(update_fields=["status"])
                refunded_count += 1
                
        except Exception as e:
            logger.error(
                "Failed to refund session %s: %s",
                session.id,
                str(e)
            )

    logger.info(
        "handle_unaccepted_sessions completed: %d sessions refunded",
        refunded_count
    )
    
    return f"Refunded {refunded_count} unaccepted sessions"


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3}
)
def expire_requested_sessions(self, *args, **kwargs) -> str:
    """
    Expire sessions that were requested but never accepted.
    
    Sessions that remain in 'requested' status past the threshold
    are refunded and marked as expired.
    """
    threshold = timezone.now() - timedelta(hours=1)

    sessions = InteractiveSession.objects.filter(
        status='requested',
        scheduled_at__slot_start_time__lt=threshold
    ).select_related('trainee')

    expired_count = 0

    for session in sessions:
        try:
            with transaction.atomic():
                session.status = 'refunded'

                if session.trainee and hasattr(session.trainee, "get_profile_data"):
                    profile = session.trainee.get_profile_data
                    if profile:
                        old_balance = profile.balance
                        profile.balance += session.fees
                        profile.save(update_fields=["balance"])
                        
                        logger.info(
                            "Expired requested session %s: trainee=%s, fees=%s, balance: %s -> %s",
                            session.id,
                            session.trainee.id,
                            session.fees,
                            old_balance,
                            profile.balance
                        )

                session.save(update_fields=["status"])
                expired_count += 1
                
        except Exception as e:
            logger.error(
                "Failed to expire session %s: %s",
                session.id,
                str(e)
            )

    logger.info(
        "expire_requested_sessions completed: %d sessions expired",
        expired_count
    )
    
    return f"Expired {expired_count} requested sessions"
