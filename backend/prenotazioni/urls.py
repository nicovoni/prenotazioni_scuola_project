from rest_framework import routers
from .views import PrenotazioneViewSet, prenota_laboratorio
from django.urls import path, include
router = routers.DefaultRouter()
router.register(r'prenotazioni', PrenotazioneViewSet)
urlpatterns = [
	path('prenota/', prenota_laboratorio, name='prenota_laboratorio'),
	path('', include(router.urls)),
]
