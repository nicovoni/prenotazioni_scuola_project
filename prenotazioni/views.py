from django.contrib.auth import get_user_model

def setup_amministratore(request):
    """View di setup amministratore e prima configurazione."""
    from django.contrib.auth import get_user_model
    from django.contrib import messages
    from django.shortcuts import render, redirect
    from .models import Risorsa, InformazioniScuola
    User = get_user_model()
    # Mostra il wizard se NON esiste alcun utente admin
    if not User.objects.filter(is_superuser=True).exists():
        # If a logged-in user exists and was promoted to staff as the first user,
        # skip the user-creation step and prefill admin email.
        step = request.GET.get('step', None)

        # Decide default step: if logged-in staff (but not superuser) -> start at school step
        if request.user.is_authenticated and request.user.is_staff and not request.user.is_superuser:
            default_step = 'school'
            skip_user_creation = True
        else:
            default_step = 1
            skip_user_creation = False

        # Normalize numeric steps to integers so templates comparing with integer work
        if step in ('1', '2', '3'):
            step = int(step)

        step = step or default_step

        # Prepare forms expected by the template
        from .forms import AdminUserForm, SchoolInfoForm
        form_admin = AdminUserForm()
        school_instance = InformazioniScuola.objects.filter(id=1).first()
        form_school = SchoolInfoForm(instance=school_instance)

        context = {
            'step': step,
            'skip_user_creation': skip_user_creation,
            'form_admin': form_admin,
            'form_school': form_school
        }

        # If skipping creation, provide admin email in context
        if skip_user_creation:
            context['admin_email'] = request.user.email

        if request.method == 'POST':
            # Step 1: Crea admin (only when not skipping user creation)
            if 'step1' in request.POST and not skip_user_creation:
                username = request.POST.get('username')
                email = request.POST.get('email')
                password = request.POST.get('password')
                if username and email and password:
                    if User.objects.filter(username=username).exists():
                        messages.error(request, 'Username già esistente.')
                    elif User.objects.filter(email=email).exists():
                        messages.error(request, 'Email già esistente.')
                    else:
                        # create as staff (we'll promote to superuser after setup completion)
                        user = User.objects.create_user(username=username, email=email, password=password, is_staff=True)
                        messages.success(request, 'Utente amministratore creato! Ora puoi configurare la scuola.')
                        return redirect('/setup/?step=school')
                else:
                    messages.error(request, 'Compila tutti i campi.')
                context['step'] = '1'
            # Step school: salva info scuola
            elif 'step_school' in request.POST:
                nome = request.POST.get('nome')
                codice = request.POST.get('codice_meccanografico')
                sito = request.POST.get('sito_web')
                indirizzo = request.POST.get('indirizzo')
                if nome and indirizzo:
                    InformazioniScuola.objects.update_or_create(id=1, defaults={
                        'nome_completo_scuola': nome,
                        'codice_meccanografico_scuola': codice or '',
                        'sito_web_scuola': sito or '',
                        'indirizzo_scuola': indirizzo
                    })
                    messages.success(request, 'Informazioni scuola salvate!')

                    # If skipping user creation, promote the logged-in staff user to superuser
                    if skip_user_creation and request.user.is_authenticated:
                        try:
                            request.user.is_superuser = True
                            request.user.is_staff = True
                            request.user.save()
                            messages.success(request, 'Il tuo account è stato promosso ad amministratore.')
                        except Exception:
                            messages.error(request, 'Impossibile promuovere l\'utente a superuser automaticamente.')

                    return redirect('/setup/?step=device')
                else:
                    messages.error(request, 'Compila i campi obbligatori.')
                context['step'] = 'school'
            # Step device e risorse: puoi aggiungere qui la logica per dispositivi e risorse
        return render(request, 'prenotazioni/configurazione_sistema.html', context)
    # Se esiste almeno un admin, redirect alla home
    return redirect('home')
"""
Views Django per la nuova architettura del sistema di prenotazioni.

Aggiornate per supportare la nuova struttura database e servizi migliorati.
"""

from django.views.generic.edit import View
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from rest_framework import viewsets, generics
from rest_framework.decorators import action
from django.contrib.auth import get_user_model

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Risorsa, Dispositivo, Prenotazione, ConfigurazioneSistema, SessioneUtente, LogSistema, NotificaUtente, UbicazioneRisorsa, CategoriaDispositivo, StatoPrenotazione, InformazioniScuola
)
from .forms import (
    ConfigurationForm, SchoolInfoForm, UserProfileForm, PinVerificationForm, EmailLoginForm, DeviceWizardForm, BookingForm, ConfirmDeleteForm, RisorseConfigurazioneForm
)
from .services import (
    ConfigurationService, UserSessionService, EmailService, BookingService,
    NotificationService, ResourceService, SystemService,
    SystemInitializer
)
from .serializers import (
    ResourceSerializer, DeviceSerializer, BookingSerializer
)


# =====================================================
# VISTE PRINCIPALI E DASHBOARD
# =====================================================

class HomeView(LoginRequiredMixin, View):
    """Homepage del sistema con dashboard personalizzato."""
    def get(self, request):
        """Mostra dashboard personalizzato per ruolo."""
        user = request.user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        from .models import Risorsa, Prenotazione
        from django.db import connection
        # Reset solo se il database è davvero vuoto
        utenti = User.objects.count()
        risorse = Risorsa.objects.count()
        prenotazioni = Prenotazione.objects.count()
        if utenti == 0 and risorse == 0 and prenotazioni == 0:
            with connection.cursor() as cursor:
                table_names = connection.introspection.table_names()
                for table in table_names:
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
            return redirect('setup_amministratore')

        context = {}

        if user.is_staff:
            # Dashboard admin
            stats = SystemService.get_system_stats()
            recent_bookings = Prenotazione.objects.filter(
                cancellato_il__isnull=True
            ).select_related('utente', 'risorsa').only('id', 'utente', 'risorsa', 'inizio', 'fine', 'stato').order_by('-inizio')[:5]
            recent_logs = LogSistema.objects.only('id', 'livello', 'messaggio', 'timestamp').order_by('-timestamp')[:10]

            context = {
                'stats': stats,
                'recent_bookings': recent_bookings,
                'is_admin': True
            }

        else:
            # Dashboard utente normale
            my_bookings = Prenotazione.objects.filter(
                utente=user,
                cancellato_il__isnull=True
            ).select_related('risorsa').only('id', 'risorsa', 'inizio', 'fine', 'stato').order_by('-inizio')[:3]

            available_resources = ResourceService.get_available_resources().only('id', 'nome', 'tipo', 'localizzazione')[:5]

            context = {
                'my_bookings': my_bookings,
                'available_resources': available_resources,
                'is_admin': False
            }

        # Informazioni scuola
        try:
            context['school_info'] = InformazioniScuola.ottieni_istanza()
        except Exception:
            context['school_info'] = None

        return render(request, 'home.html', context)


@login_required
def health_check(request):
    """Endpoint health check per monitoring."""
    try:
        # Test database connection
        Prenotazione.objects.count()
        
        # Test configuration
        config_status = ConfigurationService.get_config('SYSTEM_VERSION', 'unknown')
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': config_status,
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


# =====================================================
# CONFIGURAZIONE E SETUP SISTEMA
# =====================================================

class ConfigurazioneSistemaView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vista per configurazione iniziale e gestione configurazioni."""
    def test_func(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # Consenti accesso se utente è admin oppure se non esistono admin
        return self.request.user.is_staff or not User.objects.filter(is_superuser=True).exists()
    
    def get(self, request):
        """Mostra stato configurazione sistema."""
        # Controlla se sistema già configurato
        if not Risorsa.objects.exists():
            return self._render_setup_wizard(request)

        # Sistema già configurato - mostra gestione configurazioni
        configs = ConfigurazioneSistema.objects.only('id', 'chiave_configurazione', 'valore_configurazione', 'tipo_configurazione').order_by('tipo_configurazione', 'chiave_configurazione')
        paginator = Paginator(configs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'configs': page_obj.object_list,
            'config_types': ConfigurazioneSistema.TIPO_CONFIGURAZIONE
        }
        return render(request, 'admin/configurazioni.html', context)

    def post(self, request):
        """Gestisce creazione/modifica configurazioni."""
        action = request.POST.get('action')

        if action == 'create':
            form = ConfigurationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Configurazione creata con successo.')
            else:
                messages.error(request, 'Errore nella creazione della configurazione.')

        elif action == 'update':
            config_id = request.POST.get('config_id')
            config = get_object_or_404(ConfigurazioneSistema, id=config_id)
            form = ConfigurationForm(request.POST, instance=config)
            if form.is_valid():
                form.save()
                messages.success(request, 'Configurazione aggiornata con successo.')
            else:
                messages.error(request, 'Errore nell\'aggiornamento della configurazione.')

        elif action == 'delete':
            config_id = request.POST.get('config_id')
            config = get_object_or_404(ConfigurazioneSistema, id=config_id)
            if config.configurazione_modificabile:
                config.delete()
                messages.success(request, 'Configurazione eliminata.')
            else:
                messages.error(request, 'Questa configurazione non può essere eliminata.')

        elif action == 'initialize':
            # Inizializza sistema
            success, message = SystemInitializer.initialize_system()
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)

        return redirect('admin:configurazioni')

    def _render_setup_wizard(self, request):
        """Render wizard di setup iniziale."""
        step = request.GET.get('step', '1')

        if step == '1':
            # Configurazione scuola
            school_info, _ = InformazioniScuola.objects.get_or_create(id=1)
            form = SchoolInfoForm(instance=school_info)

        elif step == '2':
            # Configurazione dispositivi
            form = DeviceWizardForm()
            dispositivi = Dispositivo.objects.all().order_by('marca', 'nome')

        elif step == '3':
            # Configurazione risorse
            num_risorse = request.session.get('num_risorse', 3)
            dispositivi_disponibili = Dispositivo.objects.all()
            form = RisorseConfigurazioneForm(
                num_risorse=num_risorse,
                dispositivi_disponibili=dispositivi_disponibili
            )
        
        context = {
            'step': step,
            'form': form,
            'dispositivi': dispositivi if step == '2' else None
        }
        
        return render(request, 'admin/setup_wizard.html', context)


class AdminOperazioniView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vista operazioni amministrative."""
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get(self, request):
        """Mostra dashboard operazioni admin."""
        stats = SystemService.get_system_stats()
        
        # Prossime prenotazioni
        upcoming_bookings = Prenotazione.objects.filter(
            inizio__gte=timezone.now(),
            cancellato_il__isnull=True
        ).select_related('utente', 'risorsa').only('id', 'utente', 'risorsa', 'inizio', 'fine', 'stato').order_by('inizio')[:5]

        # Risorse in manutenzione
        resources_maintenance = Risorsa.objects.filter(manutenzione=True).only('id', 'nome', 'tipo', 'localizzazione')[:5]

        # Notifiche in attesa
        pending_notifications = NotificaUtente.objects.filter(
            stato='pending'
        ).select_related('utente').only('id', 'utente', 'titolo', 'messaggio', 'stato', 'creato_il').order_by('-creato_il')[:5]
        
        context = {
            'stats': stats,
            'upcoming_bookings': upcoming_bookings,
            'resources_maintenance': resources_maintenance,
            'pending_notifications': pending_notifications
        }
        
        return render(request, 'admin/operazioni.html', context)
    
    def post(self, request):
        """Gestisce azioni amministrative."""
        action = request.POST.get('action')
        
        if action == 'cleanup':
            cleaned = SystemService.cleanup_expired_data()
            messages.success(request, f'Pulizia completata: {cleaned}')
        
        elif action == 'send_notifications':
            NotificationService.send_pending_notifications()
            messages.success(request, 'Notifiche in coda inviate.')
        
        elif action == 'generate_report':
            SystemService.generate_system_report()
            # Qui potresti salvare il report o inviarlo via email
            messages.success(request, 'Report sistema generato.')
        
        return redirect('admin:operazioni')


# =====================================================
# GESTIONE UTENTI E PROFILI
# =====================================================

class UserProfileView(LoginRequiredMixin, View):
    """Gestione profilo utente."""
    
    def get(self, request):
        """Mostra profilo utente."""
        user = request.user
        profile = getattr(user, 'profilo_utente', None)

        context = {
            'user': user,
            'profile': profile,
            'recent_bookings': BookingService.get_user_bookings(user)[:5]
        }
        
        return render(request, 'users/profile.html', context)
    
    def post(self, request):
        """Aggiorna profilo utente."""
        user = request.user
        profile = getattr(user, 'profilo_utente', None)

        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profilo aggiornato con successo.')
        else:
            messages.error(request, 'Errore nell\'aggiornamento del profilo.')
        
        return redirect('users:profile')


class EmailLoginView(View):
    """Login tramite email con PIN."""
    
    def get(self, request):
        """Mostra form login email."""
        form = EmailLoginForm()
        return render(request, 'registration/email_login.html', {'form': form})
    
    def post(self, request):
        """Processa richiesta PIN."""
        form = EmailLoginForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            
            try:
                User = get_user_model()
                user = User.objects.get(email=email)

                if not user.is_active:
                    messages.error(request, 'Account disattivato.')
                    return redirect('email_login')

                # Genera PIN e crea sessione
                pin = UserSessionService.generate_pin()
                session = UserSessionService.create_session(
                    user=user,
                    tipo='login_pin',
                    email_destinazione=email,
                    pin=pin
                )

                # Invia email
                success, error = EmailService.send_pin_email(user, pin)
                if success:
                    # Save the model's token field name
                    request.session['login_session_token'] = str(getattr(session, 'token_sessione', getattr(session, 'token', '')))
                    messages.success(request, 'PIN inviato via email. Controlla la tua casella di posta.')
                    return redirect('verify_pin')
                else:
                    messages.error(request, f'Errore invio email: {error}')

            except User.DoesNotExist:
                messages.error(request, 'Email non registrata nel sistema.')
        
        return render(request, 'registration/email_login.html', {'form': form})


class PinVerificationView(View):
    """Verifica PIN per login."""
    
    def get(self, request):
        """Mostra form verifica PIN."""
        if 'login_session_token' not in request.session:
            messages.error(request, 'Sessione scaduta. Riprova il login.')
            return redirect('email_login')
        
        form = PinVerificationForm()
        return render(request, 'registration/verify_pin.html', {'form': form})
    
    def post(self, request):
        """Verifica PIN."""
        form = PinVerificationForm(request.POST)
        
        if form.is_valid():
            pin = form.cleaned_data['pin']
            token = request.session.get('login_session_token')
            
            if token:
                success, message = UserSessionService.verify_session(token, pin)
                
                if success:
                    # Login automatico
                    from django.contrib.auth import login
                    # Retrieve the session model by its token field
                    session = SessioneUtente.objects.get(token_sessione=token)
                    login(request, session.utente_sessione)
                    
                    # Pulisci sessione
                    del request.session['login_session_token']
                    
                    messages.success(request, 'Accesso effettuato con successo!')
                    return redirect('home')
                else:
                    messages.error(request, message)
            else:
                messages.error(request, 'Sessione non valida.')
        
        return render(request, 'registration/verify_pin.html', {'form': form})


# =====================================================
# PRENOTAZIONI
# =====================================================

class PrenotaResourceView(LoginRequiredMixin, View):
    """Creazione nuova prenotazione."""
    
    def get(self, request):
        """Mostra form prenotazione."""
        form = BookingForm(user=request.user)
        risorse = ResourceService.get_available_resources()

        context = {
            'form': form,
            'resources': risorse,
            'is_edit': False
        }

        return render(request, 'prenotazioni/prenota.html', context)

    def post(self, request):
        """Processa creazione prenotazione."""
        form = BookingForm(request.POST, user=request.user)

        if form.is_valid():
            # Crea prenotazione
            success, result = BookingService.create_booking(
                utente=request.user,
                risorsa_id=form.cleaned_data['risorsa'].id,
                quantita=form.cleaned_data['quantita'],
                inizio=form.cleaned_data['inizio'],
                fine=form.cleaned_data['fine'],
                scopo=form.cleaned_data.get('scopo', ''),
                note=form.cleaned_data.get('note', ''),
                priorita=form.cleaned_data['priorita'],
                setup_needed=form.cleaned_data['setup_needed'],
                cleanup_needed=form.cleaned_data['cleanup_needed']
            )

            if success:
                messages.success(request, 'Prenotazione creata con successo!')
                return redirect('bookings:lista')
            else:
                messages.error(request, f'Errore: {result}')
        else:
            messages.error(request, 'Correggi gli errori nel form.')

        risorse = ResourceService.get_available_resources()
        context = {
            'form': form,
            'resources': risorse,
            'is_edit': False
        }

        return render(request, 'prenotazioni/prenota.html', context)


class ListaPrenotazioniView(LoginRequiredMixin, View):
    """Lista prenotazioni con filtri."""
    
    def get(self, request):
        """Mostra lista prenotazioni."""
        user = request.user
        
        # Base queryset
        if user.is_staff:
            bookings = Prenotazione.objects.all()
            is_admin_view = True
        else:
            bookings = Prenotazione.objects.filter(utente=user)
            is_admin_view = False

        # Filtri
        status_filter = request.GET.get('status', '')
        resource_filter = request.GET.get('resource', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        if status_filter:
            bookings = bookings.filter(stato__nome=status_filter)

        if resource_filter:
            bookings = bookings.filter(risorsa__id=resource_filter)

        if date_from:
            bookings = bookings.filter(inizio__date__gte=date_from)

        if date_to:
            bookings = bookings.filter(fine__date__lte=date_to)

        # Escludi cancellate per vista normale
        if not request.GET.get('include_cancelled'):
            bookings = bookings.filter(cancellato_il__isnull=True)

        # Ordinamento
        order_by = request.GET.get('order_by', '-inizio')
        bookings = bookings.select_related('utente', 'risorsa').only('id', 'utente', 'risorsa', 'inizio', 'fine', 'stato').order_by(order_by)

        # Paginazione
        paginator = Paginator(bookings, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Opzioni filtri
        context = {
            'page_obj': page_obj,
            'bookings': page_obj.object_list,
            'is_admin_view': is_admin_view,
            'status_choices': StatoPrenotazione.objects.all(),
            'resource_choices': Risorsa.objects.all(),
            'current_filters': {
                'status': status_filter,
                'resource': resource_filter,
                'date_from': date_from,
                'date_to': date_to,
                'order_by': order_by
            }
        }
        
        return render(request, 'prenotazioni/lista.html', context)


class EditPrenotazioneView(LoginRequiredMixin, View):
    """Modifica prenotazione esistente."""
    
    def get(self, request, pk):
        """Mostra form modifica."""
        prenotazione = get_object_or_404(Prenotazione, pk=pk)

        # Controllo permessi
        if not prenotazione.can_be_modified_by(request.user):
            messages.error(request, 'Non hai i permessi per modificare questa prenotazione.')
            return redirect('bookings:lista')

        # Pre-compila form
        initial_data = {
            'risorsa': prenotazione.risorsa,
            'data': prenotazione.inizio.date(),
            'ora_inizio': prenotazione.inizio.time(),
            'ora_fine': prenotazione.fine.time(),
            'quantita': prenotazione.quantita,
            'scopo': prenotazione.scopo,
            'note': prenotazione.note,
            'priorita': prenotazione.priorita,
            'setup_needed': prenotazione.setup_needed,
            'cleanup_needed': prenotazione.cleanup_needed
        }

        form = BookingForm(initial=initial_data, user=request.user, prenotazione_id=pk)
        risorse = ResourceService.get_available_resources()

        context = {
            'form': form,
            'booking': prenotazione,
            'resources': risorse,
            'is_edit': True
        }

        return render(request, 'prenotazioni/prenota.html', context)

    def post(self, request, pk):
        """Processa modifica prenotazione."""
        prenotazione = get_object_or_404(Prenotazione, pk=pk)

        # Controllo permessi
        if not prenotazione.can_be_modified_by(request.user):
            messages.error(request, 'Non hai i permessi per modificare questa prenotazione.')
            return redirect('bookings:lista')

        form = BookingForm(request.POST, user=request.user, prenotazione_id=pk)

        if form.is_valid():
            # Aggiorna prenotazione
            success, result = BookingService.update_booking(
                booking_id=pk,
                utente=request.user,
                inizio=form.cleaned_data['inizio'],
                fine=form.cleaned_data['fine'],
                quantita=form.cleaned_data['quantita'],
                scopo=form.cleaned_data.get('scopo', ''),
                note=form.cleaned_data.get('note', ''),
                priorita=form.cleaned_data['priorita'],
                setup_needed=form.cleaned_data['setup_needed'],
                cleanup_needed=form.cleaned_data['cleanup_needed']
            )

            if success:
                messages.success(request, 'Prenotazione aggiornata con successo!')
                return redirect('bookings:lista')
            else:
                messages.error(request, f'Errore: {result}')
        else:
            messages.error(request, 'Correggi gli errori nel form.')

        risorse = ResourceService.get_available_resources()
        context = {
            'form': form,
            'booking': prenotazione,
            'resources': risorse,
            'is_edit': True
        }

        return render(request, 'prenotazioni/prenota.html', context)


class DeletePrenotazioneView(LoginRequiredMixin, View):
    """Elimina prenotazione."""

    def get(self, request, pk):
        """Mostra conferma eliminazione."""
        prenotazione = get_object_or_404(Prenotazione, pk=pk)

        # Controllo permessi
        if not prenotazione.can_be_cancelled_by(request.user):
            messages.error(request, 'Non hai i permessi per eliminare questa prenotazione.')
            return redirect('bookings:lista')

        form = ConfirmDeleteForm()

        context = {
            'form': form,
            'booking': prenotazione
        }

        return render(request, 'prenotazioni/delete_confirm.html', context)

    def post(self, request, pk):
        """Processa eliminazione."""
        prenotazione = get_object_or_404(Prenotazione, pk=pk)

        # Controllo permessi
        if not prenotazione.can_be_cancelled_by(request.user):
            messages.error(request, 'Non hai i permessi per eliminare questa prenotazione.')
            return redirect('bookings:lista')

        form = ConfirmDeleteForm(request.POST)

        if form.is_valid():
            # Elimina prenotazione
            success, result = BookingService.cancel_booking(
                booking_id=pk,
                utente=request.user,
                reason="Eliminata dall'utente"
            )

            if success:
                messages.success(request, 'Prenotazione eliminata con successo!')
            else:
                messages.error(request, f'Errore: {result}')
        else:
            messages.error(request, 'Devi confermare per procedere.')

        return redirect('bookings:lista')


# =====================================================
# RISORSE E DISPOSITIVI
# =====================================================

class ResourceListView(LoginRequiredMixin, View):
    """Lista risorse disponibili."""
    
    def get(self, request):
        """Mostra lista risorse con filtri."""
        resource_type = request.GET.get('type', '')
        location = request.GET.get('location', '')
        
        query = Risorsa.objects.filter(attivo=True)

        if resource_type:
            query = query.filter(tipo=resource_type)

        if location:
            query = query.filter(ubicazione__id=location)

        resources = query.select_related('ubicazione').only('id', 'nome', 'tipo', 'localizzazione').order_by('tipo', 'nome')

        # Paginazione
        paginator = Paginator(resources, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'resources': page_obj.object_list,
            'resource_types': Risorsa.TIPO_RISORSA,
            'locations': UbicazioneRisorsa.objects.filter(attivo=True),
            'current_filters': {
                'type': resource_type,
                'location': location
            }
        }
        
        return render(request, 'resources/lista.html', context)


class DeviceListView(LoginRequiredMixin, View):
    """Lista dispositivi disponibili."""
    
    def get(self, request):
        """Mostra lista dispositivi con filtri."""
        device_type = request.GET.get('type', '')
        category = request.GET.get('category', '')
        status = request.GET.get('status', 'disponibile')
        
        query = Dispositivo.objects.filter(attivo=True)

        if device_type:
            query = query.filter(tipo=device_type)

        if category:
            query = query.filter(categoria__id=category)

        if status:
            query = query.filter(stato=status)

        devices = query.select_related('categoria').only('id', 'nome', 'tipo', 'marca', 'categoria', 'stato').order_by('tipo', 'marca', 'nome')

        # Paginazione
        paginator = Paginator(devices, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'devices': page_obj.object_list,
            'device_types': Dispositivo.TIPO_DISPOSITIVO,
            'categories': CategoriaDispositivo.objects.filter(attiva=True),
            'status_choices': Dispositivo._meta.get_field('stato').choices,
            'current_filters': {
                'type': device_type,
                'category': category,
                'status': status
            }
        }
        
        return render(request, 'devices/lista.html', context)


# =====================================================
# API REST
# =====================================================


from rest_framework.pagination import PageNumberPagination

class SmallResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 20

class BookingViewSet(viewsets.ModelViewSet):
    """API REST per prenotazioni ottimizzata."""
    queryset = Prenotazione.objects.all().select_related('utente', 'risorsa').only('id', 'utente', 'risorsa', 'inizio', 'fine', 'stato')
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['utente', 'risorsa', 'stato']
    search_fields = ['scopo']
    pagination_class = SmallResultsSetPagination

    def get_queryset(self):
        """Filtra prenotazioni per utente."""
        user = self.request.user
        if user.is_staff:
            return Prenotazione.objects.all().select_related('utente', 'risorsa').only('id', 'utente', 'risorsa', 'inizio', 'fine', 'stato')
        else:
            return Prenotazione.objects.filter(utente=user).select_related('utente', 'risorsa').only('id', 'utente', 'risorsa', 'inizio', 'fine', 'stato')

    def perform_create(self, serializer):
        """Crea prenotazione associandola all'utente."""
        serializer.save(utente=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancella prenotazione."""
        booking = self.get_object()

        if not hasattr(booking, 'can_be_cancelled_by') or not booking.can_be_cancelled_by(request.user):
            return Response({'error': 'Non autorizzato'}, status=403)

        success, message = BookingService.cancel_booking(
            booking_id=pk,
            utente=request.user,
            reason="Cancellata via API"
        )

        if success:
            return Response({'message': message})
        else:
            return Response({'error': message}, status=400)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approva prenotazione (solo admin)."""
        if not request.user.is_staff:
            return Response({'error': 'Solo amministratori'}, status=403)

        booking = self.get_object()
        if hasattr(booking, 'approve'):
            booking.approve(request.user)

        return Response({'message': 'Prenotazione approvata'})



class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """API REST per risorse ottimizzata (solo lettura)."""
    queryset = Risorsa.objects.filter(attivo=True).select_related('ubicazione').only('id', 'nome', 'tipo', 'localizzazione')
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo', 'attivo']
    search_fields = ['nome']
    pagination_class = SmallResultsSetPagination



class DeviceViewSet(viewsets.ReadOnlyModelViewSet):
    """API REST per dispositivi ottimizzata (solo lettura)."""
    queryset = Dispositivo.objects.filter(attivo=True).select_related('categoria').only('id', 'nome', 'tipo', 'marca', 'categoria', 'stato')
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo', 'stato']
    search_fields = ['nome']
    pagination_class = SmallResultsSetPagination


class SystemStatsView(generics.GenericAPIView):
    """API per statistiche sistema."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Restituisce statistiche sistema."""
        if not request.user.is_staff:
            return Response({'error': 'Solo amministratori'}, status=403)
        
        stats = SystemService.get_system_stats()
        return Response(stats)


# =====================================================
# VIEW WRAPPER PER COMPATIBILITÀ
# =====================================================

def configurazione_sistema(request):
    """Wrapper view per compatibilità."""
    view = ConfigurazioneSistemaView.as_view()
    return view(request)


def admin_operazioni(request):
    """Wrapper view per compatibilità."""
    view = AdminOperazioniView.as_view()
    return view(request)


def prenota_laboratorio(request):
    """Wrapper view per compatibilità."""
    view = PrenotaResourceView.as_view()
    return view(request)


def lista_prenotazioni(request):
    """Wrapper view per compatibilità."""
    view = ListaPrenotazioniView.as_view()
    return view(request)


def edit_prenotazione(request, pk):
    """Wrapper view per compatibilità."""
    view = EditPrenotazioneView.as_view()
    return view(request, pk=pk)


def delete_prenotazione(request, pk):
    """Wrapper view per compatibilità."""
    view = DeletePrenotazioneView.as_view()
    return view(request, pk=pk)


def database_viewer(request):
    """Wrapper view per visualizzazione database (solo admin)."""
    if not request.user.is_staff:
        messages.error(request, 'Accesso negato. Solo gli amministratori possono visualizzare il database.')
        return redirect('home')
    
    # Statistiche dettagliate
    stats = SystemService.get_system_stats()
    
    # Dati completi
    User = get_user_model()
    utenti = User.objects.all().order_by('username')
    risorse = Risorsa.objects.all().select_related('ubicazione')
    dispositivi = Dispositivo.objects.all().select_related('categoria').order_by('marca', 'nome')
    prenotazioni = Prenotazione.objects.all().select_related('utente', 'risorsa', 'stato').order_by('-inizio')[:100]
    logs = LogSistema.objects.order_by('-timestamp')[:50]
    
    context = {
        'stats': stats,
        'utenti': utenti,
        'risorse': risorse,
        'dispositivi': dispositivi,
        'prenotazioni': prenotazioni,
        'logs': logs,
        'is_admin_view': True
    }
    return render(request, 'admin/database_viewer.html', context)
