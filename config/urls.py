
from django.contrib import admin
from django.urls import path, include
from .views import home, health_check
from .views_login import custom_login
from .views_email_login import email_login, verify_pin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('prenotazioni.urls', namespace='prenotazioni')),  # file prenotazioni/urls.py
    path('accounts/email-login/', email_login, name='email_login'),
    path('accounts/verify-pin/', verify_pin, name='verify_pin'),
    path('accounts/login/', custom_login, name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('health/', health_check, name='health_check'),
    path('', home, name='home'),
]
