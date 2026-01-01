"""
Celery tasks for profile operations.
"""
import logging

from celery import shared_task

from profiles.cashout import run_safe_cashout


logger = logging.getLogger('gymgem.celery')


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=120,
    retry_kwargs={"max_retries": 3},
)
def run_safe_cashout_task(self, *args, **kwargs) -> str:
    """
    Celery task wrapper for run_safe_cashout.
    
    Includes automatic retry with exponential backoff.
    """
    logger.info("Starting cashout task")
    
    try:
        run_safe_cashout()
        logger.info("Cashout task completed successfully")
        return "Cashout completed successfully"
    except Exception as e:
        logger.error("Cashout task failed: %s", str(e))
        raise
