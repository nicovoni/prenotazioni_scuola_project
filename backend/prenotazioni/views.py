from rest_framework import viewsets
from .models import Prenotazione, Risorsa
from .serializers import PrenotazioneSerializer
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.db.models import Sum
from django.core.mail import send_mail
from django.conf import settings

class PrenotazioneViewSet(viewsets.ModelViewSet):
    queryset = Prenotazione.objects.all()
    serializer_class = PrenotazioneSerializer

@login_required
def prenota_laboratorio(request):
    risorse = Risorsa.objects.filter(tipo='lab')
    messaggio = None
    success = False
    # preserve form values for UX
    preserved = {'laboratorio': '', 'data': '', 'ora_inizio': '', 'ora_fine': '', 'quantita': '1'}

    if request.method == 'POST':
        laboratorio_id = request.POST.get('laboratorio')
        data = request.POST.get('data')
        ora_inizio = request.POST.get('ora_inizio')
        ora_fine = request.POST.get('ora_fine')
        quantita_val = request.POST.get('quantita')
        preserved = {'laboratorio': laboratorio_id or '', 'data': data or '', 'ora_inizio': ora_inizio or '', 'ora_fine': ora_fine or '', 'quantita': quantita_val or '1'}
        errori = []

        if not laboratorio_id:
            errori.append("Seleziona un laboratorio.")
        if not data:
            errori.append("Seleziona una data.")
        if not ora_inizio or not ora_fine:
            errori.append("Seleziona orario di inizio e fine.")

        inizio = fine = None
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

        # Se non ci sono errori formali, procedi con il controllo disponibilità
        if not errori and laboratorio_id and inizio and fine:
            quantita_richiesta = int(quantita_val or 1)
            risorsa = Risorsa.objects.get(id=laboratorio_id)
            totale = risorsa.quantita_totale or 1

            # Somma prenotazioni sovrapposte
            overlapping = Prenotazione.objects.filter(risorsa_id=laboratorio_id).filter(
                inizio__lt=fine, fine__gt=inizio
            )
            somma_occupata = overlapping.aggregate(Sum('quantita'))['quantita__sum'] or 0
            disponibile = totale - somma_occupata

            if quantita_richiesta > disponibile:
                errori.append(f"Disponibilità insufficiente: richieste {quantita_richiesta}, disponibili {disponibile}.")
                messaggio = "<br>".join(errori)
            else:
                Prenotazione.objects.create(
                    utente=request.user,
                    risorsa_id=laboratorio_id,
                    quantita=quantita_richiesta,
                    inizio=inizio,
                    fine=fine
                )
                # tenta di inviare conferma via email (non bloccante)
                try:
                    subject = f"Conferma prenotazione: {risorsa.nome}"
                    message = (
                        f"Ciao {request.user.first_name or request.user.username},\n\n"
                        f"La tua prenotazione per {risorsa.nome} è stata confermata.\n"
                        f"Data: {inizio.date()}\n"
                        f"Orario: {inizio.time().strftime('%H:%M')} - {fine.time().strftime('%H:%M')}\n"
                        f"Quantità: {quantita_richiesta}\n\n"
                        "Grazie per aver utilizzato il sistema di prenotazioni. Buona giornata!"
                    )
                    send_mail(subject=subject, message=message, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[request.user.email], fail_silently=True)
                except Exception:
                    pass
                success = True
                messaggio = "Prenotazione effettuata con successo! Ti abbiamo inviato una mail di conferma."
        else:
            if not success:
                # se ci sono errori (o non tutti i campi sono popolati), mostra gli errori
                messaggio = "<br>".join(errori) if errori else None

    return render(request, 'prenotazioni/prenota.html', {'risorse': risorse, 'messaggio': messaggio, 'preserved': preserved, 'success': success})


@login_required
def lista_prenotazioni(request):
    # mostra le prenotazioni dell'utente corrente ordinate per data
    prenotazioni = Prenotazione.objects.filter(utente=request.user).order_by('-inizio')
    return render(request, 'prenotazioni/lista.html', {'prenotazioni': prenotazioni})


@login_required
def edit_prenotazione(request, pk):
    try:
        p = Prenotazione.objects.get(pk=pk)
    except Prenotazione.DoesNotExist:
        messages.error(request, 'Prenotazione non trovata.')
        return redirect('lista_prenotazioni')
    if p.utente != request.user:
        messages.error(request, 'Non hai i permessi per modificare questa prenotazione.')
        return redirect('lista_prenotazioni')
    # semplice form simile a prenota_laboratorio
    if request.method == 'POST':
        data = request.POST.get('data')
        ora_inizio = request.POST.get('ora_inizio')
        ora_fine = request.POST.get('ora_fine')
        quantita = int(request.POST.get('quantita') or 1)
        try:
            inizio = timezone.datetime.strptime(f"{data} {ora_inizio}", "%Y-%m-%d %H:%M")
            fine = timezone.datetime.strptime(f"{data} {ora_fine}", "%Y-%m-%d %H:%M")
            inizio = timezone.make_aware(inizio)
            fine = timezone.make_aware(fine)
            # controllo base: fine>inizio
            if fine <= inizio:
                messages.error(request, 'Orario di fine deve essere successivo all\'inizio.')
                return redirect('edit_prenotazione', pk=pk)
            # controllo disponibilità (escludendo la stessa prenotazione)
            overlapping = Prenotazione.objects.filter(risorsa=p.risorsa).exclude(pk=p.pk).filter(inizio__lt=fine, fine__gt=inizio)
            somma_occupata = overlapping.aggregate(Sum('quantita'))['quantita__sum'] or 0
            disponibile = (p.risorsa.quantita_totale or 1) - somma_occupata
            if quantita > disponibile:
                messages.error(request, f'Disponibilità insufficiente: richieste {quantita}, disponibili {disponibile}.')
                return redirect('edit_prenotazione', pk=pk)
            # salva
            p.inizio = inizio
            p.fine = fine
            p.quantita = quantita
            p.save()
            messages.success(request, 'Prenotazione aggiornata.')
            return redirect('lista_prenotazioni')
        except Exception:
            messages.error(request, 'Dati non validi.')
            return redirect('edit_prenotazione', pk=pk)
    # GET: mostra form precompilato
    preserved = {'laboratorio': p.risorsa.id, 'data': p.inizio.date().isoformat(), 'ora_inizio': p.inizio.time().strftime('%H:%M'), 'ora_fine': p.fine.time().strftime('%H:%M'), 'quantita': p.quantita}
    risorse = Risorsa.objects.filter(tipo='lab')
    return render(request, 'prenotazioni/edit.html', {'prenotazione': p, 'preserved': preserved, 'risorse': risorse})


@login_required
def delete_prenotazione(request, pk):
    try:
        p = Prenotazione.objects.get(pk=pk)
    except Prenotazione.DoesNotExist:
        messages.error(request, 'Prenotazione non trovata.')
        return redirect('lista_prenotazioni')
    if p.utente != request.user:
        messages.error(request, 'Non hai i permessi per eliminare questa prenotazione.')
        return redirect('lista_prenotazioni')
    if request.method == 'POST':
        p.delete()
        messages.success(request, 'Prenotazione eliminata.')
        return redirect('lista_prenotazioni')
    return render(request, 'prenotazioni/delete_confirm.html', {'prenotazione': p})
