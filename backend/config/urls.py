
from django.contrib import admin
from django.urls import path, include
from .views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('prenotazioni.urls')),  # file prenotazioni/urls.py
    path('accounts/', include('django.contrib.auth.urls')),
    path('', home, name='home'),
]
