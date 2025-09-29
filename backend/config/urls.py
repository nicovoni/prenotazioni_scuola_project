
from django.contrib import admin
from django.urls import path, include
from .views import home
from .views_login import custom_login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('prenotazioni.urls')),  # file prenotazioni/urls.py
    path('accounts/login/', custom_login, name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', home, name='home'),
]
