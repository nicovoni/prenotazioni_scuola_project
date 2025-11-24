
from rest_framework import routers
from .views import BookingViewSet, prenota_laboratorio, lista_prenotazioni, edit_prenotazione, delete_prenotazione, database_viewer, configurazione_sistema, admin_operazioni, setup_amministratore
from django.urls import path, include
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
    path('configurazione-sistema/', login_required(admin_required(configurazione_sistema)), name='configurazione_sistema'),
    path('admin-operazioni/', login_required(admin_required(admin_operazioni)), name='admin_operazioni'),
    path('setup/', setup_amministratore, name='setup_amministratore'),
    path('', include(router.urls)),
]
