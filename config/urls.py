from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/dashboard/', include('keys.urls_dashboard')),
    path('api/keys/', include('keys.urls')),
    path('api/setup/', include('keys.urls_setup')),
]
