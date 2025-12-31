import logging
from django.db import transaction
from django.utils import timezone

from profiles.models import Profile, CashoutReport
from profiles.lock import RedisLock

logger = logging.getLogger(__name__)

MIN_BALANCE = 100
LOCK_KEY = "cashout:global:lock"
LOCK_TTL = 300  # 5 minutes


def run_safe_cashout():
    """
    Safe cashout service using Redis lock.
    No model changes required.
    Prevents:
      - parallel execution
      - double cashout
      - partial updates
    """

    now = timezone.now()
    today = now.date()

    # 🔒 GLOBAL LOCK (prevents multiple workers running cashout together)
    try:
        with RedisLock(LOCK_KEY, ttl=LOCK_TTL):

            logger.info("Cashout lock acquired")

            with transaction.atomic():

                # Don't use `select_related` with `select_for_update` when the
                # FK is nullable (creates an outer join). Use `prefetch_related`
                # to fetch `account` in a separate query and avoid FOR UPDATE
                # on an outer join (causes NotSupportedError on some DBs).
                profiles = (
                    Profile.objects
                    .filter(profile_type__in=("trainer", "store"), status="active")
                    .select_for_update(skip_locked=True)  # DB-level lock
                    .prefetch_related("account")
                )

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

                    # 🛑 Prevent double cashout (using existing reports)
                    already_cashed = CashoutReport.objects.filter(
                        profile=profile,
                        cashed_out_at__date=today,
                    ).exists()

                    if already_cashed:
                        logger.info(
                            "Profile %s already cashed out today", profile.id
                        )
                        continue

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
                        "Cashout successful for profile %s (amount=%s)",
                        profile.id,
                        balance_value,
                    )

            logger.info("Cashout job finished successfully")

    except RuntimeError:
        # Lock not acquired → another worker already running it
        logger.warning("Cashout already running, skipping this execution")
