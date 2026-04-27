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





