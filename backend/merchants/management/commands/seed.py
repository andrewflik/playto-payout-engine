# merchants/management/commands/seed.py

import uuid
from django.core.management.base import BaseCommand
from django.db import transaction
from merchants.models import Merchant
from ledger.models import LedgerEntry
from payouts.models import Payout
from core.constants import LedgerEntryType, PayoutStatus


class Command(BaseCommand):
    help = 'Seed database with merchants and credit history'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')
        with transaction.atomic():
            self._create_merchants()
        self.stdout.write(self.style.SUCCESS('Done! Database seeded.'))

    def _create_merchants(self):
        merchants_data = [
            {
                'name': 'Raj Sharma',
                'email': 'raj@designstudio.in',
                'credits': [
                    (500000, 'Payment from Acme Corp USA'),
                    (300000, 'Payment from Beta LLC USA'),
                    (750000, 'Payment from Gamma Inc USA'),
                ],
            },
            {
                'name': 'Priya Mehta',
                'email': 'priya@devcraft.in',
                'credits': [
                    (1000000, 'Payment from TechStart USA'),
                    (450000,  'Payment from Delta Corp USA'),
                ],
            },
            {
                'name': 'Arjun Nair',
                'email': 'arjun@pixelworks.in',
                'credits': [
                    (800000, 'Payment from Epsilon LLC USA'),
                    (600000, 'Payment from Zeta Inc USA'),
                    (200000, 'Payment from Eta Corp USA'),
                ],
            },
        ]

        for data in merchants_data:
            merchant, created = Merchant.objects.get_or_create(
                email=data['email'],
                defaults={'name': data['name']}
            )

            if created:
                self.stdout.write(f'  Created merchant: {merchant.name}')
                self._create_credits(merchant, data['credits'])
                self._create_sample_payouts(merchant)
            else:
                self.stdout.write(f'  Skipped (exists): {merchant.name}')

    def _create_credits(self, merchant, credits):
        for amount_paise, note in credits:
            LedgerEntry.objects.create(
                merchant=merchant,
                entry_type=LedgerEntryType.CREDIT,
                amount_paise=amount_paise,
                reference_id=uuid.uuid4(),
                note=note,
            )
            self.stdout.write(
                f'    Credit: ₹{amount_paise // 100} — {note}'
            )

    def _create_sample_payouts(self, merchant):
        payout = Payout.objects.create(
            merchant=merchant,
            amount_paise=100000,
            bank_account_id='HDFC_001',
            status=PayoutStatus.COMPLETED,
            idempotency_key=str(uuid.uuid4()),
            attempts=1,
        )
        LedgerEntry.objects.create(
            merchant=merchant,
            entry_type=LedgerEntryType.DEBIT,
            amount_paise=100000,
            reference_id=payout.id,
            note='Payout to HDFC ····0001',
        )
        self.stdout.write(f'    Payout (completed): ₹1000')

        # failed payout with refund
        failed_payout = Payout.objects.create(
            merchant=merchant,
            amount_paise=50000,
            bank_account_id='ICICI_002',
            status=PayoutStatus.FAILED,
            idempotency_key=str(uuid.uuid4()),
            attempts=3,
        )
        LedgerEntry.objects.create(
            merchant=merchant,
            entry_type=LedgerEntryType.DEBIT,
            amount_paise=50000,
            reference_id=failed_payout.id,
            note='Payout to ICICI ····0002',
        )
        LedgerEntry.objects.create(
            merchant=merchant,
            entry_type=LedgerEntryType.CREDIT,
            amount_paise=50000,
            reference_id=failed_payout.id,
            note='Refund: payout failed after 3 attempts',
        )
        self.stdout.write(f'    Payout (failed + refunded): ₹500')