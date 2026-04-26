'''
    ledger ki enteries should never be deleted
    toh i used the field on_delete

    one to many from merchant table  -> ledger_ebtry table

    one to many: Merchant → LedgerEntry
'''

import uuid
from django.db import models
from django.db.models import Q
from core.constants import LedgerEntryType


class LedgerEntry(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    merchant = models.ForeignKey(
        'merchants.Merchant',
        on_delete=models.PROTECT,    
        related_name='ledger_entries'
    )
    entry_type = models.CharField(
        max_length=10,
        choices=LedgerEntryType.CHOICES
    )
    amount_paise = models.BigIntegerField()  # +ve always
    reference_id = models.UUIDField(
        null=True,
        blank=True
    )
    note = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # i put a unique constraint on these 2 avoid duplicate refunds
        # if somehow 2 workers get the same payouts to process 
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_paise__gt=0),  # check → condition
                name='ledger_amount_always_positive'
            ),
            models.UniqueConstraint(
                fields=['reference_id', 'entry_type'],
                name='unique_reference_entry_type'
            ),
        ]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merchant', 'entry_type']),
            models.Index(fields=['merchant', 'created_at']),
        ]

    def __str__(self):
        return f"{self.entry_type} {self.amount_paise} paise — {self.merchant}"