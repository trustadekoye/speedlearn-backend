from rest_framework import serializers
from .models import PlatformAccess


class PlatformAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformAccess
        fields = ["id", "amount", "reference", "status", "payment_date"]
        read_only_fields = ["status", "payment_date", "reference"]
