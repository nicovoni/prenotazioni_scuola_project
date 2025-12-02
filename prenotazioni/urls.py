
from rest_framework import routers
from .views import BookingViewSet, prenota_laboratorio, lista_prenotazioni, edit_prenotazione, delete_prenotazione, database_viewer, admin_operazioni, setup_amministratore, lookup_unica, debug_devices, debug_create_test_device, sanity_check
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test

app_name = 'prenotazioni'

router = routers.DefaultRouter()
router.register(r'prenotazioni', BookingViewSet)

# Decoratori di sicurezza per view sensibili
admin_required = user_passes_test(lambda u: u.is_staff)

urlpatterns = [
    path('prenota/', login_required(prenota_laboratorio), name='prenota_laboratorio'),
    path('mie-prenotazioni/', login_required(lista_prenotazioni), name='lista_prenotazioni'),
    path('prenotazione/<int:pk>/edit/', login_required(edit_prenotazione), name='edit_prenotazione'),
    path('prenotazione/<int:pk>/delete/', login_required(delete_prenotazione), name='delete_prenotazione'),
    path('database-viewer/', login_required(admin_required(database_viewer)), name='database_viewer'),
    path('configurazione-sistema/', lambda request: redirect('prenotazioni:setup_amministratore'), name='configurazione_sistema'),
    path('admin-operazioni/', login_required(admin_required(admin_operazioni)), name='admin_operazioni'),
    path('setup/', setup_amministratore, name='setup_amministratore'),
    path('lookup_unica/', lookup_unica, name='lookup_unica'),
    path('debug/devices/', debug_devices, name='debug_devices'),
    path('debug/devices/create_test/', debug_create_test_device, name='debug_create_test_device'),
    path('debug/sanity/', sanity_check, name='sanity_check'),
    path('', include(router.urls)),
]
