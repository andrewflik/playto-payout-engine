## 1. The Ledger Calculation

```python
    available_balance = LedgerEntry.objects.filter(
        merchant_id=merchant_id
    ).aggregate(
        total_credits=Sum(
            'amount_paise',
            filter=Q(entry_type=LedgerEntryType.CREDIT)
        ),
        total_debits=Sum(
            'amount_paise',
            filter=Q(entry_type=LedgerEntryType.DEBIT)
        ),
    )
```
I calculate the available balance dyanmically everytime. I actually thoguht of storing a static **balance column** in merchants table, but then there would be 2 source of balance (1 from the merchants table that we store, the other calculated using merchants ledger CREDIT/DEBIT). But to be more accurate and i read somewhere in financial systems a ledger system is usually the one source of truth and is prefered. 

So everytime balance is queries I get the merrchants_id and query his/her CREDIT/DEBIT then simple maths 
    -> *avail_balance = CREDIT - DEBIT*



## 2. The Locks

Heres the code that prevents overdrawing of balance. (p.s : sorry for the hinglish comments)
```python
########## CRITICAL SECTION ###########
########## LOCK liya ##################
try:
    with transaction.atomic():

        # row level lock kiya select_for_uddapte se
        # either hojyga commit or rollback

        merchant = Merchant.objects.select_for_update().get(
            id=merchant_id
        )

        # ab isko pay krna h, so get the balance
        result = LedgerEntry.objects.filter(
            merchant_id=merchant_id
        ).aggregate(
            credits=Sum(
                'amount_paise',
                filter=Q(entry_type=LedgerEntryType.CREDIT)
            ),
            debits=Sum(
                'amount_paise',
                filter=Q(entry_type=LedgerEntryType.DEBIT)
            ),
        )
        # negative nhi hoga bal so 0 kra
        total = (result['credits'] or 0) - (result['debits'] or 0)

        # funds held in pending or processing payouts
        held = Payout.objects.filter(
            merchant_id=merchant_id,
            status__in=PayoutStatus.HELD_STATUSES
        ).aggregate(
            total=Sum('amount_paise')
        )['total'] or 0

        available_bal = total - held

        # agr paisa kam h avail_bal se -> insuffiencent bal
        if available_bal < amount_paise:
            return Response(
                {'error': 'Insufficient balance'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # create payout here
        payout = Payout.objects.create(
            merchant=merchant,
            amount_paise=amount_paise,
            bank_account_id=bank_account_id,
            status=PayoutStatus.PENDING, # by def pending m jyga -> process krne ke baad status change hoga
            idempotency_key=idempotency_key,
        )

        # debit ledger m entry kri
        LedgerEntry.objects.create(
            merchant=merchant,
            entry_type=LedgerEntryType.DEBIT,
            amount_paise=amount_paise,
            reference_id=payout.id, # one more thing ref_id -> payout ki id rhegi so i can trace back the transacation
            note = f'Payout to {bank_account_id}', # usually note rhta h transacation m toh theres that field
        )

except IntegrityError:
    # except agr hum pauche mtlb unique vle constraint m issue hua
    # so prbably there exists combo of {merch_id, idem_key} ka
    # toh i return the existing payout object data
    existing = Payout.objects.get(
        merchant_id=merchant_id,
        idempotency_key=idempotency_key
    )
    return Response(
        PayoutSerializer(existing).data,
        status=status.HTTP_200_OK
    )
```

The lock acquired here is throught the djaongo fn -> *select_for_update()* -> it basically rows locks on the merchants record, now the lock is held until the whole transacation commits or rolls back, so this prevents any other upcoming or concurrecnt transaction from modifying anything. technically speaking we are serializing balance calculation, then payout creation, avoiding any race conditions/overdraw of available balance.

Overall, transaction.atomic() ensures all the DB operations commit together or roll back, select_for_update() is used to acuiqre the lock so no 2 concurrent request modify simentenously.

## 3. The Idempotency

we use an idempotency_key in the request to ensure that duplicate payout req with {merchant_id, idem_key} return the same result without creating multiple payouts. Theres a unique_indexing constraint on {merchant_id, idem_key}.

### Working
1. DB query Check: before processing a new payout, we query the **payout** table for existing record with same {merchabt_id, idem_key} that was within 24 hrs(acc to the challange).
```python
########### idempotency check ###########
try:
    existing = Payout.objects.get(
        merchant_id=merchant_id,
        idempotency_key=idempotency_key,
        # key expiry added after 24hrs
        created_at__gte=timezone.now() - timedelta(hours=24) 
    )
    return Response(
        PayoutSerializer(existing).data,
        status=status.HTTP_200_OK
    )
except Payout.DoesNotExist:
    pass
```
2. Unique indexing: db has a unique_constrant on {merchant, idem_key}.

```python
unique_together = ('merchant', 'idempotency_key')
```
we can prevent duplicate insertion at db level.

#### Now the mid flight question.
 1. The first request is inside the **tranasaction.atomic()** section, so at this point the new record exists but iusnt visible to others.
 2. Now comes the second request, it performs the same idempotecy query, since first one hasnt commited yet, the query returns Payout.DoesNotExit as seen in the code below.
 3. Race condiotn handling: both requests try to create a pyout with the same *idem_key*, but the unique constirant cause the later one second one to raise an exception Integrity error, code above catches it and finds the existing record which is commited by now.


 ```python
except IntegrityError:
    # except agr hum pauche mtlb unique vle constraint m issue hua
    # so prbably there exists combo of {merch_id, idem_key} ka
    # toh i return the existing payout object data
    existing = Payout.objects.get(
        merchant_id=merchant_id,
        idempotency_key=idempotency_key
    )
    return Response(
        PayoutSerializer(existing).data,
        status=status.HTTP_200_OK
    )
```

**In hinglish i commented that if we reach to this part of code then i am the idempotent request so i return back the same thing. hence this ensure Idempotency  the second request gets the same payout object as the first overdrawing or duplicating**.


## 3. The State Machine (my fav part, please check the diagram/flow ive uploaded on github)

First of all i love compiler design, anyway i took inspiration from that and designed this state machine flow. The state machine is defined in constants.py

 ```python
VALID_TRANSITIONS = {
    PENDING:    [PROCESSING],
    PROCESSING: [COMPLETED, FAILED],
    COMPLETED:  [],   # terminal
    FAILED:     [],   # terminal
}
```
FAILED has no outgoing transitions. It is terminal.(pls refer the diagram)

### The enforcment
The check that blocks FAILED → COMPLETED is in models.py:
 ```python
def transition_to(self, new_status):
    allowed = PayoutStatus.VALID_TRANSITIONS.get(self.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Illegal transition: {self.status} → {new_status}. "
            f"Allowed from {self.status}: {allowed}"
        )
    self.status = new_status
    self.save(update_fields=['status', 'updated_at'])
```

The block happens at this line:

 ```python
if new_status not in allowed:
    raise ValueError(...)
```

btw i wrote this fn insdie model to enforce state machine rules at the point where state changes.

## 4. The AI Audit

### Issue 1
While I was trying to figure out the retrying part from celery i asked chatgpt to write my a template to process stuck payouts. 


**The AI proposed manually changing stuck payouts from PROCESSING back to PENDING so they could be reprocessed.** 

```python
# AI's broken idea (pseudocode):
stuck = Payout.objects.filter(
    status=PayoutStatus.PROCESSING,
    updated_at__lt=cutoff
)
for payout in stuck:
    payout.status = PayoutStatus.PENDING  # VIOLATES STATE MACHINE
    payout.save()
```

having designed the whole state machine, this was a little funny i mean the whole point of state machine is a strict squence that needs to be followed. Lol

Anyway the serious parts are the bug that can be caused due to this ill list some here

1. State Machine Violation: PROCESSING → PENDING is not in VALID_TRANSITIONS. The transition_to() method would raise ValueError and crash.

2. Race Condition: Even if it worked, manually resetting state after a worker crash is just plain wrong lol. The bank might have already processed the payout.

3. Idempotency (ki lag gyi) Changing the state loses the trace of what happened to the original attempt.

Okay now the fix, 

```python
with transaction.atomic():
    stuck = Payout.objects.select_for_update().filter(
        status__in=[PayoutStatus.PENDING, PayoutStatus.PROCESSING],
        updated_at__lt=cutoff
    )
    payout_ids = list(stuck.values_list('id', flat=True))
    stuck.update(updated_at=timezone.now())  # refresh, don't change state

for payout_id in payout_ids:
    process_payout.delay(str(payout_id))  # re-queue with .delay()
```

Now I need to explain one thing -> imagine a scenario ill put it in the fancy box below

```python
The celery worker picks up the payout task -> marks it as PROCESSING, made the call to bank, bank request happens successfuly, now suddenly it *crashes* midway  status is set to PROCESSING, money is debited. Now what ???

Now technically since we gave the payout.id as key to bank, any further call made to bank with the same key will give us back the exisitng/same result following the idempotency principle.

“We cannot know if the bank call succeeded after a crash, so we rely on idempotency keys to make retries safe instead of trying to detect completion.”
```

So i pickup both processing & pending tasks give the idempotency prinicpal we follow if the same payout request with PROCESSING re-queued and the call is made again nothing will happen (given that bank api follow the idempotency principle).

So overall, the fix was:

1. Timestamp Refresh: Updates updated_at so beat doesn't re-queue the same payouts forever.

2. Worker-Safe: Relies on Celery's retry mechanism and bank idempotency guarantees, not manual state changing.


### Issue 2
One more thing I caught was Celery can deliver same task twice. This happens in real systems when a worker crashes mid-execution, times out, or the broker redelivers. Layer 1 (state machine) and Layer 2 (lock) catch it most of the time — but they're not bulletproof if Worker A crashes between setting status and committing the transaction. Layer 3 is the hard guarantee.

```python
    Worker A → creates refund (+6000)
    Worker B → tries to create refund again

Why credit, not debit? The debit is created when payout is requested — protected by idempotency_key already. The refund credit is the dangerous one — Worker B could create a second +₹xyz refund.
```

So i added a unique consraint over (ref_id, credit)-> 
```python
    models.UniqueConstraint(
        fields=['reference_id'],
        condition=models.Q(entry_type='credit'),
        name='unique_refund_credit_per_payout'
    ),  
```

Overall, I added a partial unique constraint on credit entries as a third layer of protection beyond the state machine and row lock.

## Ending (Conculsion)

Thanks for this challange. I enjoyed it throughly, hope to get a shot at this I'd absoultely give it my all.
