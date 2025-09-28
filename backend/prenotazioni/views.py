from rest_framework import viewsets
from .models import Prenotazione, Risorsa
from .serializers import PrenotazioneSerializer
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages

class PrenotazioneViewSet(viewsets.ModelViewSet):
    queryset = Prenotazione.objects.all()
    serializer_class = PrenotazioneSerializer

@login_required
def prenota_laboratorio(request):
    risorse = Risorsa.objects.filter(tipo='lab')
    messaggio = None
    if request.method == 'POST':
        laboratorio_id = request.POST.get('laboratorio')
        data = request.POST.get('data')
        ora_inizio = request.POST.get('ora_inizio')
        ora_fine = request.POST.get('ora_fine')
        errori = []
        if not laboratorio_id:
            errori.append("Seleziona un laboratorio.")
        if not data:
            errori.append("Seleziona una data.")
        if not ora_inizio or not ora_fine:
            errori.append("Seleziona orario di inizio e fine.")
        if data and ora_inizio and ora_fine:
            try:
                inizio = timezone.datetime.strptime(f"{data} {ora_inizio}", "%Y-%m-%d %H:%M")
                fine = timezone.datetime.strptime(f"{data} {ora_fine}", "%Y-%m-%d %H:%M")
                inizio = timezone.make_aware(inizio)
                fine = timezone.make_aware(fine)
                if inizio < timezone.now():
                    errori.append("La data e ora di inizio devono essere nel futuro.")
                if fine <= inizio:
                    errori.append("L'orario di fine deve essere successivo a quello di inizio.")
            except Exception:
                errori.append("Data o orario non validi.")
        if not errori and laboratorio_id and data and ora_inizio and ora_fine:
            Prenotazione.objects.create(
                utente=request.user,
                risorsa_id=laboratorio_id,
                inizio=inizio,
                fine=fine
            )
            messaggio = "Prenotazione effettuata con successo!"
        else:
            messaggio = "<br>".join(errori)
    return render(request, 'prenotazioni/prenota.html', {'risorse': risorse, 'messaggio': messaggio})
