from django.db import IntegrityError, models
from django.conf import settings
from django.db import transaction
from django.utils import timezone
# Create your models here.


class Profile(models.Model):
    TYPE_CHOICES = [
        ("gym", "Gym"),
        ("trainer", "Trainer"),
        ("store", "Store"),
        ("trainee", "Trainee"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("suspended", "Suspended"),
    ]
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profiles",
        null=True,
    )
    profile_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active",null=True, blank=True)
    admin_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "profile_type"], name="uniq_account_profiletype"
            )
        ]

    def __str__(self):
        return f"{self.profile_type} Profile for {self.account}"

    @property
    def user(self):
        return self.account
    
    @property
    def get_profile_data(self):
        if self.profile_type == "trainer":
            from trainers.models import Trainer
            return Trainer.objects.filter(profile_id=self).first()
        if self.profile_type == "gym":
            from gyms.models import Gym
            return Gym.objects.filter(profile_id=self).first()
        if self.profile_type == "store":
            from stores.models import Store
            return Store.objects.filter(profile_id=self).first()
        if self.profile_type == "trainee":
            from trainees.models import Trainee
            return Trainee.objects.filter(profile=self).first()




    @classmethod
    def balance_cashout_report(cls):
        # If CashoutReport model isn't available in this module, bail out
        if "CashoutReport" not in globals():
            return []

        created_reports = []

        qs = cls.objects.filter(profile_type__in=("trainer", "store")).select_related("account")
        for profile in qs:
            pdata = getattr(profile, "get_profile_data", None)
            if not pdata:
                continue

            balance = getattr(pdata, "gems", None)
            if balance is None:
                balance = getattr(pdata, "balance", 0)

            try:
                balance_value = float(balance)
            except (TypeError, ValueError):
                continue

            if balance_value > 100:
                name = getattr(pdata, "name", None) or (
                    profile.account.get_full_name() if hasattr(profile.account, "get_full_name") else getattr(profile.account, "username", "")
                )
                mobile = getattr(pdata, "mobile", None) or getattr(profile.account, "mobile", "")
                email = getattr(profile.account, "email", "")
                address = getattr(pdata, "address", "")

                try:
                    with transaction.atomic():
                        report = CashoutReport.objects.create(
                            profile=profile,
                            name=name,
                            mobile=mobile,
                            email=email,
                            address=address,
                            balance_before=balance_value,
                            cashed_out_at=timezone.now(),
                        )
                        if hasattr(pdata, "gems"):
                            pdata.gems = 0
                            pdata.save(update_fields=["gems"])
                        elif hasattr(pdata, "balance"):
                            pdata.balance = 0
                            pdata.save(update_fields=["balance"])
                        created_reports.append(report)
                except IntegrityError:
                    continue

        return created_reports


class CashoutReport(models.Model):
    choices = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    profile = models.ForeignKey(
        "Profile",
        on_delete=models.CASCADE,
        related_name="cashout_reports",
    )
    name = models.CharField(max_length=255, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    cashed_out_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=choices, default="pending")

    class Meta:
        verbose_name = "Cashout Report"
        verbose_name_plural = "Cashout Reports"

    def __str__(self):
        return f"CashoutReport(profile={self.profile_id}, amount={self.balance_before}, at={self.cashed_out_at})"
    

    # balance_cashout_report is provided on `Profile` as a classmethod