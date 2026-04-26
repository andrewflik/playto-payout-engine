import random
from celery import shared_task
from django.db import transaction
from payouts.models import Payout
from ledger.models import LedgerEntry
from core.constants import PayoutStatus, LedgerEntryType


@shared_task(bind=True, max_retries=3)
def process_payout(self, payout_id):
    '''
        3 attemp set krdiye  MAX
        check status then go ahead with steps
        if processed toh stop
        1 atomic transaction hoga jisme i include both (fail + refund)
    '''

    try:
        with transaction.atomic():

            # lock in the payout row
            try:
                payout = Payout.objects.select_for_update().get(
                    id=payout_id
                )
            except Payout.DoesNotExist:
                # payout was deleted — nothing to do
                return

            # only pick up pending ones vrna dhoom machegi
            if payout.status != PayoutStatus.PENDING:
                print(f'Payout {payout_id} already {payout.status} — skipping')
                return

            # ── 3. transition to processing ────────────────────────
            payout.transition_to(PayoutStatus.PROCESSING)
            payout.attempts += 1
            payout.save(update_fields=['attempts', 'updated_at'])
        
        # yaha pe the idae is to release the lock toh
        # bank might take time/delays etc 
        # put the bank processing part outside

        # random sampling (70, 20, 10)
        # idea is to simulate bank call here
        res = random.choices(
            ['success', 'fail', 'hang'], [70, 20, 10]
        )

        print(f'Payout {payout_id} — outcome: {res}')
        if res[0] == 'success':
            processSuccess(payout)
        elif res[0] == 'fail':
            processFailure(payout)
        elif res[0] == 'hang':
            ############### exponential backoff logic ###############
            # pow(2, retries) countdown will raise in powers of 2

            # raise kro exception since retry exception dega
            # sp raise it manually
            raise self.retry(
                countdown = 2 ** self.request.retries,
                exc = Exception(f'Payout {payout_id} hung — retrying')
            )

    except Exception as exc:
        # agr retries attemp over -> then we refund simply
        if self.request.retries >= self.max_retries:
            print(f'Payout {payout_id} — max retries exceeded, failing')
            try:
                payout = Payout.objects.get(id=payout_id)
                processFailure(payout)
            except Payout.DoesNotExist:
                pass
        else:
            raise exc


def processSuccess(payout):
    with transaction.atomic():
        # lock lgao -> kaam kro 
        payout = Payout.objects.select_for_update().get(id=payout.id)
        # extra check
        if payout.status != PayoutStatus.PROCESSING:
            return

        payout.transition_to(PayoutStatus.COMPLETED)
        print(f'Payout {payout.id} — completed')


def processFailure(payout):
    with transaction.atomic():
        # lock lgao pphirse kaam kro
        payout = Payout.objects.select_for_update().get(id=payout.id)

        # extra check - processing vle ko hi change krna h both success and failure m
        if payout.status != PayoutStatus.PROCESSING:
            return

        # transition to fail
        # payout status change kro
        payout.transition_to(PayoutStatus.FAILED)

        # ledger m CREDIT ki entry krni h ab
        LedgerEntry.objects.create(
            merchant=payout.merchant,
            entry_type=LedgerEntryType.CREDIT,
            amount_paise=payout.amount_paise,
            reference_id=payout.id,
            note=f'Refund: payout failed after {payout.attempts} attempts',
        )

        print(f'Payout {payout.id} — failed, ₹{payout.amount_paise // 100} refunded')