from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction, IntegrityError
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404
from merchants.models import Merchant
from ledger.models import LedgerEntry
from core.constants import LedgerEntryType, PayoutStatus
from .models import Payout
from .serializers import PayoutSerializer

'''
    POST ->
        1. idem_key check kro
        2. sarie fields h proper check kro
        3. merchant should exist
        4. {idem_key, merchant_id} same payload -> check kro kya yeh PayOut exist krta h?
                                -> YES = great return the existing status
                                -> NO = process the payload
'''

class PayoutCreateView(APIView):

    def post(self, request):
        idempotency_key = request.headers.get('Idempotency-Key')

        if not idempotency_key:
            return Response(
                {'error': 'Idempotency-Key header is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        merchant_id = request.data.get('merchant_id')
        amount_paise = request.data.get('amount_paise')
        bank_account_id = request.data.get('bank_account_id')

        if not all([merchant_id, amount_paise, bank_account_id]):
            return Response(
                {'error': 'merchant_id, amount_paise, bank_account_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(amount_paise, int) or amount_paise <= 0:
            return Response(
                {'error': 'amount_paise must be a positive integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        get_object_or_404(Merchant, id=merchant_id)

        ########### idempotency check ###########
        try:
            existing = Payout.objects.get(
                merchant_id=merchant_id,
                idempotency_key=idempotency_key
            )
            return Response(
                PayoutSerializer(existing).data,
                status=status.HTTP_200_OK
            )
        except Payout.DoesNotExist:
            pass

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
                        {
                            'error': 'Insufficient balance',
                            'available_paise': available_bal,
                            'requested_paise': amount_paise,
                        },
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

        # queue m dal do for processing
        from jobs.tasks import process_payout
        process_payout.delay(str(payout.id))
        return Response(
            PayoutSerializer(payout).data,
            status=status.HTTP_201_CREATED
        )


class PayoutListView(APIView):

    # merchant ke transactions niklo throught merchant_id
    def get(self, request):
        merchant_id = request.query_params.get('merchant_id')
        if not merchant_id:
            return Response(
                {'error': 'merchant_id query param required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payouts = Payout.objects.filter(
            merchant_id=merchant_id
        ).order_by('-created_at') # new niklne h shyd

        serializer = PayoutSerializer(payouts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)