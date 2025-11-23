from rest_framework import routers
from .views import BookingViewSet, prenota_laboratorio, lista_prenotazioni, edit_prenotazione, delete_prenotazione, database_viewer, configurazione_sistema, admin_operazioni, setup_amministratore
from django.urls import path, include

app_name = 'prenotazioni'

router = routers.DefaultRouter()
router.register(r'prenotazioni', BookingViewSet)
urlpatterns = [
	path('prenota/', prenota_laboratorio, name='prenota_laboratorio'),
	path('mie-prenotazioni/', lista_prenotazioni, name='lista_prenotazioni'),
	path('prenotazione/<int:pk>/edit/', edit_prenotazione, name='edit_prenotazione'),
	path('prenotazione/<int:pk>/delete/', delete_prenotazione, name='delete_prenotazione'),
	path('database-viewer/', database_viewer, name='database_viewer'),
	path('configurazione-sistema/', configurazione_sistema, name='configurazione_sistema'),
	path('admin-operazioni/', admin_operazioni, name='admin_operazioni'),
	path('setup/', setup_amministratore, name='setup_amministratore'),
	path('', include(router.urls)),
]
