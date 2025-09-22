from rest_framework import routers
from .views import PrenotazioneViewSet
from django.urls import path, include
router=routers.DefaultRouter()
router.register(r'prenotazioni',PrenotazioneViewSet)
urlpatterns=[path('',include(router.urls))]
