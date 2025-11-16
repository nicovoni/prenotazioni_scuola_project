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

from .models import Prenotazione, Risorsa, Utente, SchoolInfo
from .serializers import PrenotazioneSerializer
from .services import BookingService, EmailService
from .forms import PrenotazioneForm, ConfirmDeleteForm, ConfigurazioneSistemaForm, AdminUserForm, SchoolInfoForm

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
    # Controllo configurazione sistema
    if not Risorsa.objects.exists():
        if request.user.is_admin():
            messages.warning(request, 'Il sistema non è ancora configurato. Vai alla configurazione per impostarlo.')
        else:
            messages.error(request, 'Il sistema non è ancora stato configurato dall\'amministratore.')
            return redirect('lista_prenotazioni')

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
            'school_info': {
                'name': 'Informazioni Scuola',
                'data': list(SchoolInfo.objects.all()),
                'fields': ['nome_scuola', 'indirizzo', 'telefono', 'email_scuola', 'sito_web', 'codice_scuola']
            },
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


def configurazione_sistema(request):
    """
    Wizard per la configurazione iniziale del sistema.

    Prima accesso: crea admin + risorse.
    Successivi: solo risorse (se admin connesso).
    """
    # Se primo accesso (no utenti), procedi senza auth
    primo_accesso = not Utente.objects.exists()

    if not primo_accesso:
        # Richiede login se utenti esistono ma non loggato
        if not request.user.is_authenticated:
            messages.error(request, 'Devi accedere per riconfigurare il sistema.')
            return redirect('login')
        if not request.user.is_staff:
            messages.error(request, 'Solo amministratori possono riconfigurare il sistema.')
            return redirect('home')
        # Se già configurato, mostra pagina esistente
        if Risorsa.objects.exists():
            risorse = Risorsa.objects.all().order_by('nome')
            return render(request, 'prenotazioni/configurazione_gia_eseguita.html', {'risorse': risorse})

    if request.method == 'POST':
        if 'step1' in request.POST:  # Creazione admin (solo primo accesso)
            form_admin = AdminUserForm(request.POST)
            if form_admin.is_valid():
                email = form_admin.cleaned_data['email']
                # Controlla se utente già esiste
                if Utente.objects.filter(email=email).exists():
                    messages.error(request, 'Un utente con questa email esiste già.')
                    return render(request, 'prenotazioni/configurazione_sistema.html', {
                        'step': primo_accesso and 1 or 'admin',
                        'form_admin': form_admin,
                    })

                # Crea admin user con password temporanea
                admin_user = Utente.objects.create_user(
                    username=email,  # usa email come username temporaneamente
                    email=email,
                    password=None,  # password verrà settata dopo verifica PIN
                    ruolo='admin'
                )
                admin_user.is_active = False  # disattivato fino a verifica PIN
                admin_user.save()

                # Invia PIN via email
                success, message = EmailService.send_admin_pin_email(admin_user)

                if success:
                    # Crea messaggio di successo specifico per admin
                    admin_welcome_message = (
                        f"Tì sei stato designato come amministratore del sistema di prenotazioni. "
                        f"Un PIN di verifica è stato inviato all'email {email}. "
                        f"Una volta verificato, potrai completare la configurazione del sistema."
                    )
                    messages.success(request, admin_welcome_message)

                    # Se primo accesso, passa direttamente a passo scuola senza attesa della verifica
                    # Questo permette admin di completare config subito dopo invio PIN
                    return render(request, 'prenotazioni/configurazione_sistema.html', {
                        'step': 'school',
                        'form_school': SchoolInfoForm(),
                        'admin_created': True,
                        'admin_email': email
                    })
                else:
                    # Se errore invio email, elimina utente creato e mostra errore
                    admin_user.delete()
                    messages.error(request, f'Errore nell\'invio dell\'email di verifica: {message}')
                    logger.error(f"Errore email admin per {email}: {message}")
                    return render(request, 'prenotazioni/configurazione_sistema.html', {
                        'step': primo_accesso and 1 or 'admin',
                        'form_admin': form_admin,
                    })

            else:
                return render(request, 'prenotazioni/configurazione_sistema.html', {
                    'step': primo_accesso and 1 or 'admin',
                    'form_admin': form_admin,
                })

        elif 'step_school' in request.POST:  # Informazioni scuola
            school_info, created = SchoolInfo.objects.get_or_create(id=1)
            form_school = SchoolInfoForm(request.POST, instance=school_info)
            if form_school.is_valid():
                form_school.save()
                messages.success(request, 'Informazioni scuola salvate con successo.')
                # Passa a passo risorse
                return render(request, 'prenotazioni/configurazione_sistema.html', {
                    'step': 2,
                    'form_num': ConfigurazioneSistemaForm(),
                })
            else:
                return render(request, 'prenotazioni/configurazione_sistema.html', {
                    'step': 'school',
                    'form_school': form_school,
                })

        elif 'step2' in request.POST:  # Numero risorse
            form_num = ConfigurazioneSistemaForm(request.POST)
            if form_num.is_valid():
                request.session['num_risorse'] = form_num.cleaned_data['num_risorse']
                # Passa a passo 3
                form_dettagli = ConfigurazioneSistemaForm(num_risorse=form_num.cleaned_data['num_risorse'])
                return render(request, 'prenotazioni/configurazione_sistema.html', {
                    'step': 3,
                    'form_num': form_num,
                    'form_dettagli': form_dettagli,
                })
            else:
                return render(request, 'prenotazioni/configurazione_sistema.html', {
                    'step': 2,
                    'form_num': form_num,
                })

        elif 'step3' in request.POST:  # Dettagli risorse
            num_risorse = request.session.get('num_risorse')
            if not num_risorse:
                messages.error(request, 'Sessione scaduta. Ricomincia.')
                return redirect('configurazione_sistema')

            form_dettagli = ConfigurazioneSistemaForm(request.POST, num_risorse=num_risorse)
            if form_dettagli.is_valid():
                # Crea risorse
                risorse_create = []
                for i in range(1, num_risorse + 1):
                    nome = form_dettagli.cleaned_data[f'nome_{i}']
                    tipo = form_dettagli.cleaned_data[f'tipo_{i}']
                    quantita = form_dettagli.cleaned_data[f'quantita_{i}']
                    risorse_create.append(Risorsa(nome=nome, tipo=tipo, quantita_totale=quantita))

                # Valida nomi unici
                nomi = [r.nome for r in risorse_create]
                if len(nomi) != len(set(nomi)):
                    messages.error(request, 'Nomi risorse unici richiesti.')
                    return render(request, 'prenotazioni/configurazione_sistema.html', {
                        'step': 3,
                        'form_dettagli': form_dettagli,
                    })

                # Salva
                Risorsa.objects.bulk_create(risorse_create)
                if 'num_risorse' in request.session:
                    del request.session['num_risorse']
                messages.success(request, f'Configurazione completata! {num_risorse} risorse create.')
                if primo_accesso:
                    messages.info(request, 'Ora puoi accedere con l\'account amministratore creato.')
                    return redirect('login')
                else:
                    return redirect('home')
            else:
                return render(request, 'prenotazioni/configurazione_sistema.html', {
                    'step': 3,
                    'form_dettagli': form_dettagli,
                })

    # GET: determina passo
    if primo_accesso:
        return render(request, 'prenotazioni/configurazione_sistema.html', {
            'step': 1,
            'form_admin': AdminUserForm(),
        })
    else:
        # Reconfigurazione: inizia con informazioni scuola
        school_info, created = SchoolInfo.objects.get_or_create(id=1)
        return render(request, 'prenotazioni/configurazione_sistema.html', {
            'step': 'school',
            'form_school': SchoolInfoForm(instance=school_info),
        })


@login_required
def admin_operazioni(request):
    """
    View per le operazioni amministrative avanzate, come reset completo.

    Accesso riservato agli amministratori.
    """
    if not request.user.is_admin():
        messages.error(request, 'Accesso riservato agli amministratori.')
        return redirect('lista_prenotazioni')

    if request.method == 'POST' and request.POST.get('action') == 'reset':
        # Memorizza info admin corrente prima del reset
        current_admin_username = request.user.username
        current_admin_email = request.user.email

        # Reset completo: elimina TUTTI i dati tranne lasciar completare la richiesta all'admin corrente
        deleted_school_info = SchoolInfo.objects.all().delete()[0]

        # Elimina tutte le prenotazioni e risorse prima degli utenti
        deleted_prenotazioni = Prenotazione.objects.all().delete()[0]
        deleted_risorse = Risorsa.objects.all().delete()[0]

        # Crea lista di tutti gli utenti per statistica
        all_users = list(Utente.objects.all())
        total_users = len(all_users)

        # Elimina tutti gli utenti
        Utente.objects.all().delete()

        # Logout forzato dell'admin corrente (se ancora esistente)
        from django.contrib.auth import logout
        logout(request)

        messages.success(request, 'Reset completo effettuato con successo! '
                         f'Eliminati {deleted_school_info} record scuola, {total_users} utenti, {deleted_prenotazioni} prenotazioni e {deleted_risorse} risorse. '
                         'La tua sessione è stata terminata e il sistema è stato riportato allo stato iniziale. Ricarica la pagina per accedere nuovamente alla configurazione.')
        logger.info(f"Reset completo di tutti i dati effettuato da admin {current_admin_username} ({current_admin_email}): "
                   f"{deleted_school_info} school info, {total_users} utenti, {deleted_prenotazioni} prenotazioni, {deleted_risorse} risorse eliminati")

        # Reindirizza alla pagina di configurazione dopo reset
        return redirect('configurazione_sistema')

    return render(request, 'prenotazioni/admin_operazioni.html')
