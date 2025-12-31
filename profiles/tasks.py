from celery import shared_task
from profiles.cashout import run_safe_cashout


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=120,
    retry_kwargs={"max_retries": 3},
)
def run_safe_cashout_task(self, *args, **kwargs):
    run_safe_cashout()
