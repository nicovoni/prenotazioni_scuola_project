from rest_framework import viewsets
from .models import Prenotazione, Risorsa
from .serializers import PrenotazioneSerializer
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.conf import settings

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
                now = timezone.now()
                # Regole: data futura
                if inizio < now:
                    errori.append("La data e ora di inizio devono essere nel futuro.")
                # Regole: giorni di anticipo
                giorni_anticipo = settings.GIORNI_ANTICIPO_PRENOTAZIONE
                if (inizio.date() - now.date()).days < giorni_anticipo:
                    errori.append(f"La prenotazione deve essere fatta almeno {giorni_anticipo} giorni prima.")
                # Regole: orari consentiti
                orario_inizio = inizio.strftime('%H:%M')
                orario_fine = fine.strftime('%H:%M')
                if orario_inizio < settings.BOOKING_START_HOUR or orario_fine > settings.BOOKING_END_HOUR:
                    errori.append(f"Le prenotazioni sono consentite solo tra le {settings.BOOKING_START_HOUR} e le {settings.BOOKING_END_HOUR}.")
                # Regole: durata minima/massima
                durata_min = settings.DURATA_MINIMA_PRENOTAZIONE_MINUTI
                durata_max = settings.DURATA_MASSIMA_PRENOTAZIONE_MINUTI
                durata = int((fine-inizio).total_seconds() // 60)
                if durata < durata_min:
                    errori.append(f"La durata minima della prenotazione è di {durata_min} minuti.")
                if durata > durata_max:
                    errori.append(f"La durata massima della prenotazione è di {durata_max} minuti.")
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
