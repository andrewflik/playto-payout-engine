'''
    here ive defined all the constants all in once place
    :))
'''

class LedgerEntryType:
    CREDIT = 'credit'
    DEBIT = 'debit'

    CHOICES = [
        (CREDIT, 'Credit'),
        (DEBIT, 'Debit'),
    ]

class PayoutStatus:
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

    CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]

    VALID_TRANSITIONS = {
        PENDING:    [PROCESSING],
        PROCESSING: [COMPLETED, FAILED],
        COMPLETED:  [],   # terminal
        FAILED:     [],   # terminal
    }

    # fund hold status
    HELD_STATUSES = [PENDING, PROCESSING]