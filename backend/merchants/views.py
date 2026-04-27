from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from merchants.models import Merchant
from ledger.utils import get_balance_breakdown
from .serializers import BalanceSerializer, MerchantSerializer


class MerchantListView(APIView):
    def get(self, request):
        merchants = Merchant.objects.all()
        serializer = MerchantSerializer(merchants, many=True)
        return Response(serializer.data)

class MerchantBalanceView(APIView):

    def get(self, request, merchant_id):
        # 404 if no merhcant found
        get_object_or_404(Merchant, id=merchant_id)

        # get breakdown — total, held, available
        bal_details = get_balance_breakdown(merchant_id)
        
        print(bal_details)
        data = {
            'merchant_id': merchant_id,
            **bal_details # bahar nikla dict se - spreadout
        }

        serializer = BalanceSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)