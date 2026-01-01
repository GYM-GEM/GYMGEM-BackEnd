"""
Safe cashout service for trainers and stores.

Uses Redis locking to prevent concurrent execution and
database transactions to ensure atomic operations.
"""
import logging
from typing import List

from django.db import transaction
from django.utils import timezone

from profiles.models import Profile, CashoutReport
from profiles.lock import RedisLock


logger = logging.getLogger('gymgem.celery')

MIN_BALANCE: int = 100
LOCK_KEY: str = "cashout:global:lock"
LOCK_TTL: int = 300  # 5 minutes


def run_safe_cashout() -> None:
    """
    Safe cashout service using Redis lock.
    
    Prevents:
      - Parallel execution
      - Double cashout
      - Partial updates
    """
    now = timezone.now()
    today = now.date()

    try:
        with RedisLock(LOCK_KEY, ttl=LOCK_TTL):
            logger.info("Cashout lock acquired, starting processing")

            with transaction.atomic():
                # Fetch profiles with optimized query
                profiles = (
                    Profile.objects
                    .filter(profile_type__in=("trainer", "store"), status="active")
                    .select_for_update(skip_locked=True)
                    .prefetch_related("account")
                )

                processed_count = 0
                skipped_count = 0

                for profile in profiles:
                    pdata = getattr(profile, "get_profile_data", None)
                    if not pdata:
                        logger.warning("Profile %s has no profile_data", profile.id)
                        continue

                    balance = getattr(pdata, "gems", None)
                    if balance is None:
                        balance = getattr(pdata, "balance", 0)

                    try:
                        balance_value = float(balance)
                    except (TypeError, ValueError):
                        continue

                    if balance_value < MIN_BALANCE:
                        continue

                    # Prevent double cashout
                    already_cashed = CashoutReport.objects.filter(
                        profile=profile,
                        cashed_out_at__date=today,
                    ).exists()

                    if already_cashed:
                        logger.debug(
                            "Profile %s already cashed out today, skipping",
                            profile.id
                        )
                        skipped_count += 1
                        continue

                    # Create cashout report
                    CashoutReport.objects.create(
                        profile=profile,
                        name=getattr(pdata, "name", "") or profile.account.get_username(),
                        mobile=getattr(pdata, "mobile", ""),
                        email=getattr(profile.account, "email", ""),
                        address=getattr(pdata, "address", ""),
                        balance_before=balance_value,
                        cashed_out_at=now,
                    )

                    # Reset balance safely
                    if hasattr(pdata, "gems"):
                        pdata.gems = 0
                        pdata.save(update_fields=["gems"])
                    elif hasattr(pdata, "balance"):
                        pdata.balance = 0
                        pdata.save(update_fields=["balance"])

                    logger.info(
                        "Cashout successful: profile=%s, type=%s, amount=%.2f",
                        profile.id,
                        profile.profile_type,
                        balance_value,
                    )
                    processed_count += 1

            logger.info(
                "Cashout job finished: processed=%d, skipped=%d",
                processed_count,
                skipped_count
            )

    except RuntimeError:
        # Lock not acquired - another worker already running
        logger.warning("Cashout already running, skipping this execution")
