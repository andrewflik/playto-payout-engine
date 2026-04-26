from rest_framework import serializers
from .models import Payout
from ledger.models import LedgerEntry


class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = [
            'id',
            'merchant',
            'amount_paise',
            'bank_account_id',
            'status',
            'idempotency_key',
            'attempts',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'attempts',
            'created_at',
            'updated_at',
        ]


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = [
            'id',
            'entry_type',
            'amount_paise',
            'reference_id',
            'note',
            'created_at',
        ]