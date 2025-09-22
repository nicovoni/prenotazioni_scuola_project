from rest_framework import serializers
from .models import Prenotazione
class PrenotazioneSerializer(serializers.ModelSerializer):
    class Meta:
        model=Prenotazione
        fields='__all__'
