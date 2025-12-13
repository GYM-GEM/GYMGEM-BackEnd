from django.db import models

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    user = models.ForeignKey(
        'profiles.Profile',   # عدّل حسب مشروعك
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paymob_order_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    paymob_transaction_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    # Optional: what is being purchased (e.g., course enrollment)
    purpose_type = models.CharField(max_length=50, blank=True, null=True)
    purpose_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.status}"
