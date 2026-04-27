from rest_framework import serializers
from merchants.models import Merchant


class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = ['id', 'name', 'email', 'created_at']


class BalanceSerializer(serializers.Serializer):
    merchant_id = serializers.UUIDField()
    total_balance_paise = serializers.IntegerField()
    held_balance_paise = serializers.IntegerField()
    available_balance_paise = serializers.IntegerField()