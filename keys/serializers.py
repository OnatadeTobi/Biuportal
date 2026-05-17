from rest_framework import serializers


class ScanQRSerializer(serializers.Serializer):
    qr_code_id = serializers.CharField(max_length=100)
