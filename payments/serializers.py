from rest_framework import serializers
from .models import PlatformAccess


class PlatformAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformAccess
        fields = ["id", "amount", "reference", "status", "created_at", "verified_at"]
        read_only_fields = ["status", "created_at", "verified_at"]
