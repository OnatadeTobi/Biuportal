from django.urls import path

from keys.views import KeyActivityView, KeyStatusView, ScanQRView

urlpatterns = [
    path('status/', KeyStatusView.as_view(), name='key-status'),
    path('activity/', KeyActivityView.as_view(), name='key-activity'),
    path('scan/', ScanQRView.as_view(), name='key-scan'),
]
