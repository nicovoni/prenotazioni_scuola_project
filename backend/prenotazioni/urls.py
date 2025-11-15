from rest_framework import routers
from .views import PrenotazioneViewSet, prenota_laboratorio, lista_prenotazioni, edit_prenotazione, delete_prenotazione, database_viewer
from django.urls import path, include
router = routers.DefaultRouter()
router.register(r'prenotazioni', PrenotazioneViewSet)
urlpatterns = [
	path('prenota/', prenota_laboratorio, name='prenota_laboratorio'),
	path('mie-prenotazioni/', lista_prenotazioni, name='lista_prenotazioni'),
	path('prenotazione/<int:pk>/edit/', edit_prenotazione, name='edit_prenotazione'),
	path('prenotazione/<int:pk>/delete/', delete_prenotazione, name='delete_prenotazione'),
	path('database-viewer/', database_viewer, name='database_viewer'),
	path('', include(router.urls)),
]
