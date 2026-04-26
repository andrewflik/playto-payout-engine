import uuid
from django.db import models
from django.utils import timezone
from core.constants import PayoutStatus

class Payout(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    merchant = models.ForeignKey(
        'merchants.Merchant',
        on_delete=models.PROTECT,
        related_name='payouts'
    )

    amount_paise = models.BigIntegerField()
    bank_account_id = models.CharField(max_length=100)

    status = models.CharField(
        max_length=20,
        choices=PayoutStatus.CHOICES,
        default=PayoutStatus.PENDING,
        db_index=True
    )
    
    idempotency_key = models.CharField(max_length=100)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # DB-level pe hi enforce krdiya ki there will be no duplicacy of payouts
        unique_together = ('merchant', 'idempotency_key')

        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merchant', 'status']),
            models.Index(fields=['status', 'updated_at']),  # for retry worker
        ]

    def __str__(self):
        return f"Payout {self.id} — {self.status} — {self.amount_paise} paise"

    '''
        koi aur directly na change kre state of payout
        so i created this fn which follows the state machine valid trans..
    '''
    def transition_to(self, new_status):
        allowed = PayoutStatus.VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Illegal transition: {self.status} → {new_status}. "
                f"Allowed from {self.status}: {allowed}"
            )
        self.status = new_status
        self.save(update_fields=['status', 'updated_at'])