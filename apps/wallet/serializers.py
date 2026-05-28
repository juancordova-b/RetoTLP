from decimal import Decimal

from rest_framework import serializers


class DepositSerializer(serializers.Serializer):
    monto = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("0.0001"))
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)
