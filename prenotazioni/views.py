from django.views.generic.edit import TemplateResponseMixin, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from .models import Utente, Risorsa, Device, SchoolInfo
from .forms import AdminUserForm, DeviceWizardForm, SchoolInfoForm, ConfigurazioneSistemaForm, RisorseConfigurazioneForm
from .services import EmailService


class ConfigurazioneSistema(View):
    """
    Class-based view per la configurazione iniziale del sistema.

    Gestisce il wizard multi-step per setup iniziale e riconfigurazione.
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        # Se primo accesso (no utenti), procedi senza auth
        primo_accesso = not Utente.objects.exists()

        if not primo_accesso and not request.user.is_authenticated:
            messages.error(request, 'Devi accedere per riconfigurare il sistema.')
            return redirect(reverse('login'))

        if not primo_accesso and not request.user.is_admin():
            messages.error(request, 'Solo amministratori possono riconfigurare il sistema.')
            return redirect(reverse('home'))

        # Se configurazione già completata, mostra pagina info
        if Risorsa.objects.exists():
            risorse = Risorsa.objects.all().order_by('nome')
            return render(request, 'prenotazioni/configurazione_gia_eseguita.html', {'risorse': risorse})

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        """Gestisce richieste GET determinando il passo appropriato."""
        passo = self._determina_passo(request)

        if passo == 'admin':
            return self.render_step('admin', form_admin=AdminUserForm())
        elif passo == 'school':
            school_info, _ = SchoolInfo.objects.get_or_create(id=1)
            return self.render_step('school', form_school=SchoolInfoForm(instance=school_info))
        elif passo == 'device':
            dispositivi = self.get_dispositivi_safely()
            return self.render_step('device', form_device=DeviceWizardForm(),
                                  dispositivi_esistenti=dispositivi[0], db_error=dispositivi[1])
        else:
            return self.render_step(1, form_admin=AdminUserForm())

    def post(self, request):
        """Gestisce richieste POST delegando al metodo appropriato."""
        step_handlers = {
            'step1': self.handle_admin_creation,
            'step_school': self.handle_school_info,
            'add_device': self.handle_add_device,
            'remove_device': self.handle_remove_device,
            'step_device_continue': self.handle_device_continue,
            'step2': self.handle_numero_risorse,
            'step3': self.handle_dettagli_risorse,
        }

        for step_key, handler in step_handlers.items():
            if step_key in request.POST:
                return handler(request)

        # Step non riconosciuto
        messages.error(request, 'Passo configurazione non valido.')
        return redirect(reverse('prenotazioni:configurazione_sistema'))

    def handle_admin_creation(self, request):
        """Gestisce creazione utente amministratore."""
        form_admin = AdminUserForm(request.POST)
        if not form_admin.is_valid():
            return self.render_step(1, form_admin=form_admin)

        email = form_admin.cleaned_data['email']

        # Controlla duplicati
        if Utente.objects.filter(email=email).exists():
            messages.error(request, 'Un utente con questa email esiste già.')
            return self.render_step(1, form_admin=form_admin)

        # Crea admin con sistema PIN
        admin_user = Utente.objects.create_user(
            username=email, email=email, password=None, ruolo='admin'
        )
        admin_user.is_active = False
        admin_user.save()

        # Genera e invia PIN
        pin = self._generate_pin()
        self._save_pin_session(request, email, pin)
        self._send_pin_email(email, pin)

        messages.success(request,
            f"Account amministratore creato per {email}. Ti abbiamo inviato un PIN via email."
        )

        return self.render_step('school', form_school=SchoolInfoForm(), admin_created=True, admin_email=email)

    def handle_school_info(self, request):
        """Gestisce salvataggio informazioni scuola."""
        school_info, _ = SchoolInfo.objects.get_or_create(id=1)
        form_school = SchoolInfoForm(request.POST, instance=school_info)

        if not form_school.is_valid():
            return self.render_step('school', form_school=form_school)

        form_school.save()
        messages.success(request, 'Informazioni scuola salvate.')

        # Vai al passo dispositivi
        dispositivi = self.get_dispositivi_safely()
        return self.render_step('device', form_device=DeviceWizardForm(),
                              dispositivi_esistenti=dispositivi[0], db_error=dispositivi[1])

    def handle_add_device(self, request):
        """Gestisce aggiunta nuovo dispositivo."""
        try:
            form_device = DeviceWizardForm(request.POST)
            if form_device.is_valid():
                device = form_device.save()
                messages.success(request, f'Dispositivo "{device.get_display_completo()}" aggiunto.')

            dispositivi = self.get_dispositivi_safely()
            return self.render_step('device', form_device=DeviceWizardForm(),
                                  dispositivi_esistenti=dispositivi[0])

        except Exception as e:
            messages.error(request, f'Errore salvataggio dispositivo: {e}')
            return self.render_step('device', form_device=DeviceWizardForm(request.POST),
                                  dispositivi_esistenti=[], db_error=True, error_message=str(e))

    def handle_remove_device(self, request):
        """Gestisce rimozione dispositivo."""
        try:
            device_id = request.POST.get('device_id')
            device = Device.objects.get(id=device_id)
            nome = device.get_display_completo()
            device.delete()
            messages.success(request, f'Dispositivo "{nome}" rimosso.')
        except Exception as e:
            messages.error(request, f'Errore rimozione dispositivo: {e}')

        dispositivi = self.get_dispositivi_safely()
        return self.render_step('device', form_device=DeviceWizardForm(),
                              dispositivi_esistenti=dispositivi[0][0] if dispositivi[0] else [])

    def handle_device_continue(self, request):
        """Gestisce passaggio al passo successivo dopo dispositivi."""
        try:
            dispositivi = Device.objects.all().order_by('produttore', 'nome')
            if not dispositivi:
                messages.error(request, 'Devi catalogare almeno un dispositivo.')
                return self.render_step('device', form_device=DeviceWizardForm(),
                                      dispositivi_esistenti=Device.objects.all().order_by('produttore', 'nome'))

            return self.render_step(2, form_num=ConfigurazioneSistemaForm(),
                                  dispositivi_disponibili=list(dispositivi))

        except Exception as e:
            messages.error(request, f'Errore caricamento dispositivi: {e}')
            return self.render_step('device', form_device=DeviceWizardForm(),
                                  dispositivi_esistenti=[], db_error=True, error_message=str(e))

    def handle_numero_risorse(self, request):
        """Gestisce selezione numero risorse."""
        form_num = ConfigurazioneSistemaForm(request.POST)
        if not form_num.is_valid():
            return self.render_step(2, form_num=form_num)

        num_risorse = form_num.cleaned_data['num_risorse']
        request.session['num_risorse'] = num_risorse

        dispositivi = self.get_dispositivi_safely()
        if dispositivi[1]:  # db_error
            messages.warning(request, 'Catalogo dispositivi non disponibile.')

        return self.render_step(3, form_num=form_num, form_dettagli=self._get_risorse_form(num_risorse, dispositivi[0]),
                              num_risorse=num_risorse, dispositivi_disponibili=dispositivi[0],
                              num_risorse_range=list(range(1, num_risorse + 1)))

    def handle_dettagli_risorse(self, request):
        """Gestisce configurazione dettagliata risorse."""
        num_risorse = request.session.get('num_risorse')
        if not num_risorse:
            messages.error(request, 'Sessione scaduta. Ricomincia.')
            return redirect(reverse('prenotazioni:configurazione_sistema'))

        # Processa risorse
        dispositivi_disponibili = {d.id: d for d in Device.objects.all()}
        risorse_data, associazioni, errori = self._process_risorse_data(request, num_risorse, dispositivi_disponibili)

        if errori:
            for errore in errori:
                messages.error(request, errore)
            dispositivi_list = list(dispositivi_disponibili.values())
            return self.render_step(3, num_risorse=num_risorse, num_risorse_range=list(range(1, num_risorse + 1)),
                                  dispositivi_disponibili=dispositivi_list)

        # Salva tutto in una transazione
        try:
            with transaction.atomic():
                risorse_salvate = []
                for risorsa_obj, indice in zip(risorse_data, range(1, num_risorse + 1)):
                    risorsa = Risorsa.objects.create(**risorsa_obj)
                    risorse_salvate.append(risorsa)

                    # Associa dispositivi se presenti
                    dispositivi = associazioni.get(indice, [])
                    if dispositivi:
                        risorsa.dispositivi.set(dispositivi)

                if 'num_risorse' in request.session:
                    del request.session['num_risorse']

                messages.success(request, f'Configurazione completata! {len(risorse_salvate)} risorse create.')
                primo_accesso = not Utente.objects.exists()
                if primo_accesso:
                    messages.info(request, 'Ora puoi accedere con l\'account amministratore creato.')
                    return redirect(reverse('login'))
                else:
                    return redirect(reverse('home'))

        except Exception as e:
            messages.error(request, f'Errore salvataggio risorse: {e}')
            dispositivi_list = list(dispositivi_disponibili.values())
            return self.render_step(3, num_risorse=num_risorse, num_risorse_range=list(range(1, num_risorse + 1)),
                                  dispositivi_disponibili=dispositivi_list)

    def render_step(self, step, **context):
        """Rendering helper per i vari passi."""
        base_context = {'step': step}
        base_context.update(context)
        return render(self.request, 'prenotazioni/configurazione_sistema.html', base_context)

    def _determina_passo(self, request):
        """Determina il passo iniziale della configurazione."""
        if not Utente.objects.exists():
            return 'admin'  # Primo accesso
        if not SchoolInfo.objects.filter(nome__isnull=False).exists():
            return 'school'  # Informazioni scuola mancanti
        return 'device'  # Configurazione dispositivi

    def get_dispositivi_safely(self):
        """Carica dispositivi gestendo errori database."""
        try:
            dispositivi = list(Device.objects.all().order_by('produttore', 'nome'))
            return dispositivi, False
        except Exception as e:
            return [], True

    def _generate_pin(self):
        """Genera PIN monouso."""
        import random, string
        return ''.join(random.choices(string.digits, k=6))

    def _save_pin_session(self, request, email, pin):
        """Salva PIN in sessione."""
        request.session['admin_setup_email'] = email
        request.session['admin_setup_pin'] = pin
        request.session['admin_setup_pin_time'] = timezone.now().isoformat()

    def _send_pin_email(self, email, pin):
        """Invia PIN via email."""
        from config.views_email_login import send_pin_email_async
        send_pin_email_async(email, pin)

    def _get_risorse_form(self, num_risorse, dispositivi):
        """Crea form per configurazione risorse."""
        try:
            return RisorseConfigurazioneForm(num_risorse=num_risorse, dispositivi_disponibili=dispositivi)
        except Exception:
            return None

    def _process_risorse_data(self, request, num_risorse, dispositivi_disponibili):
        """Processa i dati delle risorse dal form."""
        risorse_data = []
        associazioni = {}
        errori = []

        for i in range(1, num_risorse + 1):
            nome = request.POST.get(f'nome_{i}', '').strip()
            tipo = request.POST.get(f'tipo_{i}', '').strip()
            dispositivi_selezionati = request.POST.getlist(f'dispositivi_{i}')

            # Validazioni base
            if not nome:
                errori.append(f'Nome richiesto per la risorsa {i}')
                continue
            if not tipo or tipo not in ['lab', 'carrello']:
                errori.append(f'Tipo non valido per la risorsa {i}')
                continue

            if tipo == 'carrello':
                if not dispositivi_selezionati:
                    errori.append(f'Dispositivi richiesti per il carrello {nome}')
                    continue

                dispositivi_validi, errs = self._validate_device_selection(dispositivi_selezionati, dispositivi_disponibili, nome)
                if errs:
                    errori.extend(errs)
                    continue

                risorse_data.append({
                    'nome': nome, 'tipo': tipo, 'capacita_massima': len(dispositivi_validi)
                })
                associazioni[i] = dispositivi_validi
            else:
                risorse_data.append({
                    'nome': nome, 'tipo': tipo, 'capacita_massima': None
                })
                associazioni[i] = []

        return risorse_data, associazioni, errori

    def _validate_device_selection(self, dispositivi_ids, dispositivi_disponibili, nome_risorsa):
        """Valida selezione dispositivi."""
        dispositivi_validi = []
        errori = []

        for device_id in dispositivi_ids:
            try:
                device_id_int = int(device_id)
                if device_id_int not in dispositivi_disponibili:
                    errori.append(f'Dispositivo non trovato nel carrello {nome_risorsa}')
                    break
                dispositivi_validi.append(dispositivi_disponibili[device_id_int])
            except (ValueError, TypeError):
                errori.append(f'Dispositivo non valido nel carrello {nome_risorsa}')
                break

        return dispositivi_validi, errori


# View wrapper per compatibilità
def configurazione_sistema(request):
    """Wrapper view per compatibilità backward."""
    view = ConfigurazioneSistema.as_view()
    return view(request)
