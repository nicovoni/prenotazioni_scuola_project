"""
Views per il sistema di prenotazioni scolastiche.

Gestisce le operazioni CRUD per le prenotazioni e l'interfaccia utente.
"""
import logging
from rest_framework import viewsets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Prenotazione, Risorsa, Utente
from .serializers import PrenotazioneSerializer
from .services import BookingService, EmailService
from .forms import PrenotazioneForm, ConfirmDeleteForm

logger = logging.getLogger(__name__)

class PrenotazioneViewSet(viewsets.ModelViewSet):
    queryset = Prenotazione.objects.all()
    serializer_class = PrenotazioneSerializer

@login_required
def prenota_laboratorio(request):
    """
    View per la prenotazione di risorse (laboratori e carrelli).

    Utilizza i servizi di business per validazione e creazione prenotazione.
    """
    risorse = Risorsa.objects.all().order_by('tipo', 'nome')
    messaggio = None
    success = False

    if request.method == 'POST':
        # Crea form con i dati POST
        form = PrenotazioneForm(request.POST, user=request.user)

        if form.is_valid():
            try:
                # Crea la prenotazione utilizzando il servizio
                success, result = BookingService.create_booking(
                    utente=request.user,
                    risorsa_id=form.cleaned_data['risorsa'].id,
                    quantita=form.cleaned_data['quantita'],
                    inizio=form.cleaned_data['inizio'],
                    fine=form.cleaned_data['fine']
                )

                if success:
                    messages.success(request, "Prenotazione effettuata con successo! Ti abbiamo inviato una mail di conferma.")
                    logger.info(f"Prenotazione creata dall'utente {request.user}: {result}")
                    return redirect('lista_prenotazioni')
                else:
                    messaggio = "<br>".join(result)
                    logger.warning(f"Errore creazione prenotazione per utente {request.user}: {result}")

            except Exception as e:
                messaggio = f"Errore durante la creazione della prenotazione: {str(e)}"
                logger.error(f"Errore creazione prenotazione per utente {request.user}: {e}")
        else:
            # Il form ha errori di validazione
            messaggio = "<br>".join([str(error) for error in form.non_field_errors()])
            logger.warning(f"Errore validazione form per utente {request.user}: {form.errors}")

    else:
        # GET request - inizializza form vuoto
        form = PrenotazioneForm()

    return render(request, 'prenotazioni/prenota.html', {
        'risorse': risorse,
        'messaggio': messaggio,
        'form': form,
        'success': success
    })


@login_required
def lista_prenotazioni(request):
    """
    View per visualizzare l'elenco delle prenotazioni dell'utente.

    Amministratore: mostra tutte le prenotazioni.
    Docente/altro: mostra solo le proprie prenotazioni.
    """
    if request.user.is_admin():
        prenotazioni = Prenotazione.objects.all().order_by('-inizio')
    else:
        prenotazioni = Prenotazione.objects.filter(utente=request.user).order_by('-inizio')

    logger.info(f"Elenco prenotazioni richiesto dall'utente {request.user}: {prenotazioni.count()} prenotazioni")
    return render(request, 'prenotazioni/lista.html', {'prenotazioni': prenotazioni, 'is_admin_view': request.user.is_admin()})


@login_required
def edit_prenotazione(request, pk):
    """
    View per la modifica di una prenotazione esistente.

    Utilizza i servizi di business per validazione e aggiornamento.
    """
    prenotazione = get_object_or_404(Prenotazione, pk=pk)

    # Controllo autorizzazioni: admin può modificare qualsiasi prenotazione, altri solo le proprie
    if not request.user.is_admin() and prenotazione.utente != request.user:
        messages.error(request, 'Non hai i permessi per modificare questa prenotazione.')
        logger.warning(f"Utente {request.user} ha tentato di modificare prenotazione {pk} di altro utente")
        return redirect('lista_prenotazioni')

    if request.method == 'POST':
        # Crea form con i dati POST e prenotazione esistente
        form = PrenotazioneForm(request.POST, user=request.user, prenotazione_id=pk)

        if form.is_valid():
            try:
                # Aggiorna la prenotazione utilizzando il servizio
                success, result = BookingService.update_booking(
                    prenotazione_id=pk,
                    utente=request.user,
                    inizio=form.cleaned_data['inizio'],
                    fine=form.cleaned_data['fine'],
                    quantita=form.cleaned_data['quantita']
                )

                if success:
                    messages.success(request, 'Prenotazione aggiornata con successo.')
                    logger.info(f"Prenotazione {pk} aggiornata dall'utente {request.user}")
                    return redirect('lista_prenotazioni')
                else:
                    # Mostra errori dal servizio
                    for error in result:
                        messages.error(request, error)
                    logger.warning(f"Errore aggiornamento prenotazione {pk} per utente {request.user}: {result}")

            except Exception as e:
                messages.error(request, f'Errore durante l\'aggiornamento: {str(e)}')
                logger.error(f"Errore aggiornamento prenotazione {pk} per utente {request.user}: {e}")
        else:
            # Il form ha errori di validazione
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f'{field}: {error}')
            logger.warning(f"Errore validazione form modifica prenotazione {pk} per utente {request.user}: {form.errors}")

    else:
        # GET request - inizializza form con dati esistenti
        initial_data = {
            'risorsa': prenotazione.risorsa,
            'data': prenotazione.inizio.date(),
            'ora_inizio': prenotazione.inizio.time(),
            'ora_fine': prenotazione.fine.time(),
            'quantita': prenotazione.quantita
        }
        form = PrenotazioneForm(initial=initial_data, user=request.user, prenotazione_id=pk)

    risorse = Risorsa.objects.all().order_by('tipo', 'nome')
    return render(request, 'prenotazioni/edit.html', {
        'prenotazione': prenotazione,
        'form': form,
        'risorse': risorse
    })


@login_required
def database_viewer(request):
    """
    View riservata all'amministratore per visualizzare il contenuto grezzo del database.

    Mostra tutte le tabelle principali in formato tabulare semplice.
    """
    if not request.user.is_admin():
        messages.error(request, 'Accesso riservato agli amministratori.')
        return redirect('lista_prenotazioni')

    # Recupera i dati da tutte le tabelle principali
    try:
        tables_data = {
            'utenti': {
                'name': 'Utenti',
                'data': list(Utente.objects.all().order_by('username')),
                'fields': ['username', 'first_name', 'last_name', 'email', 'ruolo', 'telefono', 'classe', 'is_active']
            },
            'risorse': {
                'name': 'Risorse',
                'data': list(Risorsa.objects.all().order_by('nome')),
                'fields': ['nome', 'tipo', 'quantita_totale']
            },
            'prenotazioni': {
                'name': 'Prenotazioni',
                'data': list(Prenotazione.objects.all().select_related('utente', 'risorsa').order_by('-inizio')),
                'fields': ['id', 'Utente', 'Risorsa', 'quantita', 'inizio', 'fine']
            }
        }
    except Exception as e:
        logger.error(f"Errore nel caricamento dati database viewer: {e}")
        messages.error(request, 'Errore nel caricamento dei dati del database.')
        return redirect('lista_prenotazioni')

    return render(request, 'prenotazioni/database_viewer.html', {
        'tables_data': tables_data
    })


@login_required
def delete_prenotazione(request, pk):
    """
    View per l'eliminazione di una prenotazione.

    Utilizza i servizi di business per l'eliminazione sicura.
    """
    prenotazione = get_object_or_404(Prenotazione, pk=pk)

    # Controllo autorizzazioni: admin può eliminare qualsiasi prenotazione, altri solo le proprie
    if not request.user.is_admin() and prenotazione.utente != request.user:
        messages.error(request, 'Non hai i permessi per eliminare questa prenotazione.')
        logger.warning(f"Utente {request.user} ha tentato di eliminare prenotazione {pk} di altro utente")
        return redirect('lista_prenotazioni')

    if request.method == 'POST':
        try:
            # Elimina la prenotazione utilizzando il servizio
            success, errors = BookingService.delete_booking(
                prenotazione_id=pk,
                utente=request.user
            )

            if success:
                messages.success(request, 'Prenotazione eliminata con successo.')
                logger.info(f"Prenotazione {pk} eliminata dall'utente {request.user}")
                return redirect('lista_prenotazioni')
            else:
                # Mostra errori dal servizio
                for error in errors:
                    messages.error(request, error)
                logger.warning(f"Errore eliminazione prenotazione {pk} per utente {request.user}: {errors}")

        except Exception as e:
            messages.error(request, f'Errore durante l\'eliminazione: {str(e)}')
            logger.error(f"Errore eliminazione prenotazione {pk} per utente {request.user}: {e}")

    return render(request, 'prenotazioni/delete_confirm.html', {'prenotazione': prenotazione})
