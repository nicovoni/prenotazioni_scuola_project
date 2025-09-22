from rest_framework import viewsets
from .models import Prenotazione
from .serializers import PrenotazioneSerializer
class PrenotazioneViewSet(viewsets.ModelViewSet):
    queryset=Prenotazione.objects.all()
    serializer_class=PrenotazioneSerializer
