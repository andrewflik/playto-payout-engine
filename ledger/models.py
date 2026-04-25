'''
    ledger ki enteries should never be deleted
    toh i used the field on_delete

    one to many from merchant table  -> ledger_ebtry table
'''

import uuid
from django.db import models


class LedgerEntry(models.Model):
    CREDIT = 'credit'
    DEBIT = 'debit'
    TYPE_CHOICES = [
        (CREDIT, 'Credit'),   # credit hua
        (DEBIT, 'Debit'),     # debit hua
    ]

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
        choices=TYPE_CHOICES
    )
    amount_paise = models.BigIntegerField()  # +ve always
    reference_id = models.UUIDField(
        null=True,
        blank=True
    )
    note = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merchant', 'entry_type']),
            models.Index(fields=['merchant', 'created_at']),
        ]

    def __str__(self):
        return f"{self.entry_type} {self.amount_paise} paise — {self.merchant}"