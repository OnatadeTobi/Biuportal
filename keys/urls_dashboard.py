from django.urls import path

from keys.views import DashboardView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
]
