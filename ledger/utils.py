from django.db.models import Sum, Q
from .models import LedgerEntry


def get_balance(merchant_id):
    """
        pehle i thought of running 2 seprate aggregate queries for
        debit/credit -> then improved to single query with filters=Q
    """
    result = LedgerEntry.objects.filter(
        merchant_id=merchant_id
    ).aggregate(
        total_credits=Sum(
            'amount_paise',
            filter=Q(entry_type=LedgerEntry.CREDIT)
        ),
        total_debits=Sum(
            'amount_paise',
            filter=Q(entry_type=LedgerEntry.DEBIT)
        ),
    )
    credits = result['total_credits'] or 0
    debits = result['total_debits'] or 0
    return credits - debits


def get_balance_breakdown(merchant_id):
    from payouts.models import Payout

    total = get_balance(merchant_id)

    held = Payout.objects.filter(
        merchant_id=merchant_id,
        status__in=[Payout.PENDING, Payout.PROCESSING]
    ).aggregate(
        total=Sum('amount_paise')
    )['total'] or 0

    return {
        'total_balance_paise': total,
        'held_balance_paise': held,
        'available_balance_paise': total - held,
    }