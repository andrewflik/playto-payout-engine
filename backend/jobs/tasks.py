import random
from celery import shared_task
from django.db import transaction
from payouts.models import Payout
from ledger.models import LedgerEntry
from core.constants import PayoutStatus, LedgerEntryType
from django.utils import timezone

@shared_task(
    bind=True,
    max_retries=3,
    acks_late=True,              
    reject_on_worker_lost=True,
)
def process_payout(self, payout_id):
    '''
        3 attemp set krdiye MAX
        check status then go ahead with steps
        if processed toh stop
        1 atomic transaction hoga jisme I include both (fail + refund)
        
        idempotency strategy:
        payout.id is sent to bank as idempotency key
        bank guarantees: same key = same result
        so retrying is always safe — no double charge
    '''

    try:
        with transaction.atomic():
            try:
                payout = Payout.objects.select_for_update().get(
                    id=payout_id
                )
            except Payout.DoesNotExist:
                return

            # if completed or failed then we skip
            if payout.status in [
                PayoutStatus.COMPLETED,
                PayoutStatus.FAILED
            ]:
                print(f'Payout {payout_id} already {payout.status} — skipping')
                return

            # print(f'process_payout start {payout_id} status={payout.status}')

            # PENDING → first attempt
            # transition to PROCESSING normally
            if payout.status == PayoutStatus.PENDING:
                payout.transition_to(PayoutStatus.PROCESSING)
                payout.attempts += 1
                payout.save(update_fields=['attempts', 'updated_at'])

            # PROCESSING → retry ya stuck recovery
            # state machine violate nahi krte — transition skip
            # idempotency key ki wajah se bank dobara charge nahi krega
            elif payout.status == PayoutStatus.PROCESSING:
                if payout.attempts >= 3:
                    # max attempts already done — give up
                    processFailure(payout)
                    return
                payout.attempts += 1
                payout.save(update_fields=['attempts', 'updated_at'])

        # yaha pe the idea is to release the lock toh
        # bank might take time/delays etc
        # put the bank processing part outside

        ### ------------ BANK PROCESSING HERE ------------ ###

        # random sampling (70, 20, 10)
        # idea is to simulate bank call here
        res = random.choices(
            ['success', 'fail', 'hang'], [70, 20, 10]
        )

        print(f'Payout {payout_id} attempt {payout.attempts} — outcome: {res[0]}')

        if res[0] == 'success':
            processSuccess(payout)
        elif res[0] == 'fail':
            processFailure(payout)
        elif res[0] == 'hang':
            ############### exponential backoff logic ###############
            # pow(2, retries) countdown will raise in powers of 2

            # raise kro exception since retry exception dega
            # so raise it manually
            raise self.retry(
                countdown = 2 ** self.request.retries,
                exc = Exception(f'Payout {payout_id} hung — retrying')
            )

    except Exception as exc:
        # agr retries attempt over -> then we refund simply
        if self.request.retries >= self.max_retries:
            print(f'Payout {payout_id} — max retries exceeded, failing')
            try:
                payout = Payout.objects.get(id=payout_id)
                # sirf PROCESSING state mein hi fail kro
                # agar koi aur state hai toh kuch mat kro
                if payout.status == PayoutStatus.PROCESSING:
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

@shared_task
def retry_stuck_payouts():
    '''
        run every 30 seconds - celery beat
        oayout that are stuck in processing over >= 30 sec
        unko requeue kro

        -- EDGE CASE --
        yha pe the AI tried to change the state machien state manually to pending,
        which technically violates our statemachien toh maine iska solution yeh nikla
        ki we should process both pending and processing given that
        idempotency principal se we should get same result.

        ek scene assume kr rha hu -> worker payout ko process kr rha tha and it crashed
        the bank opeation happened -> now since we passed the payout.id as the idempotent key
        we should always get the same result no matter what even after several retries from the back end
        so yeh affect nai krega apna result and hence no duplicay.

        - yeh retrial m state change nai krna chahiye acc. to me itll violate our state machine.
        - apne ko payout jb process krenge we will let pending & processing IN.
        - uske baad pending ka normal flow rhega, but for processing vle ko attempt krege with the same key
        there wont be any issue - given that we rely on the fact that bank knows our idem_key(has seen before the worker crashed)
        so we will get the same respons back.
    '''
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(seconds=30)

    with transaction.atomic():
        stuck = Payout.objects.select_for_update().filter(
            status__in=[PayoutStatus.PENDING, PayoutStatus.PROCESSING],
            updated_at__lt=cutoff
        )
        payout_ids = list(stuck.values_list('id', flat=True))
        # refresh updated_at so next Beat tick doesn't re-queue
        stuck.update(updated_at=timezone.now())

    for payout_id in payout_ids:
        process_payout.delay(str(payout_id))

    if payout_ids:
        print(f'Re-queued {len(payout_ids)} stuck payouts')