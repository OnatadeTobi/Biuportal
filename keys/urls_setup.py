from django.urls import path

from keys.views import QRCodeSetupView

urlpatterns = [
    path('qr-codes/', QRCodeSetupView.as_view(), name='setup-qr-codes'),
]
