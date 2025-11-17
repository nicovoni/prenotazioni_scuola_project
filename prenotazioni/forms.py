"""
Form Django per la validazione dei dati di prenotazione.
"""
from django import forms
from django.utils import timezone
from django.conf import settings
from .models import Prenotazione, Risorsa, SchoolInfo, Device


class PrenotazioneForm(forms.Form):
    """
    Form per la creazione e modifica di prenotazioni.
    """
    risorsa = forms.ModelChoiceField(
        queryset=Risorsa.objects.all(),
        empty_label="Seleziona una risorsa",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_risorsa'})
    )

    data = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': timezone.now().date().isoformat()
        })
    )

    ora_inizio = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )

    ora_fine = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )

    quantita = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'id': 'id_quantita'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.prenotazione_id = kwargs.pop('prenotazione_id', None)
        super().__init__(*args, **kwargs)

        # Imposta il queryset ordinato per tipo e nome
        self.fields['risorsa'].queryset = Risorsa.objects.all().order_by('tipo', 'nome')

    def clean(self):
        """
        Validazione complessiva del form.
        """
        cleaned_data = super().clean()
        risorsa = cleaned_data.get('risorsa')
        data = cleaned_data.get('data')
        ora_inizio = cleaned_data.get('ora_inizio')
        ora_fine = cleaned_data.get('ora_fine')
        quantita = cleaned_data.get('quantita')

        if not (risorsa and data and ora_inizio and ora_fine and quantita):
            return cleaned_data

        # Validazione specifica per tipo di risorsa
        if risorsa.tipo == 'lab':
            # Laboratori: prenotazione dell'intero laboratorio (quantità = 1)
            if quantita != 1:
                raise forms.ValidationError("Per i laboratori è possibile prenotare solo l'intero spazio.")
        elif risorsa.tipo == 'carrello':
            # Carrelli: prenotazione parziale possibile
            if quantita > risorsa.capacita_massima:
                raise forms.ValidationError(f"Quantità richiesta ({quantita}) supera la disponibilità totale ({risorsa.capacita_massima}).")

        # Crea oggetti datetime per validazione
        try:
            inizio = timezone.datetime.combine(data, ora_inizio)
            fine = timezone.datetime.combine(data, ora_fine)
            inizio = timezone.make_aware(inizio)
            fine = timezone.make_aware(fine)
            now = timezone.now()

            # Validazioni temporali
            if inizio < now:
                raise forms.ValidationError("La data e ora di inizio devono essere nel futuro.")

            giorni_anticipo = settings.GIORNI_ANTICIPO_PRENOTAZIONE
            if (inizio.date() - now.date()).days < giorni_anticipo:
                raise forms.ValidationError(f"La prenotazione deve essere fatta almeno {giorni_anticipo} giorni prima.")

            # Controllo orari consentiti
            orario_inizio = ora_inizio.strftime('%H:%M')
            orario_fine = ora_fine.strftime('%H:%M')
            if orario_inizio < settings.BOOKING_START_HOUR or orario_fine > settings.BOOKING_END_HOUR:
                raise forms.ValidationError(f"Le prenotazioni sono consentite solo tra le {settings.BOOKING_START_HOUR} e le {settings.BOOKING_END_HOUR}.")

            # Controllo durata
            durata_min = settings.DURATA_MINIMA_PRENOTAZIONE_MINUTI
            durata_max = settings.DURATA_MASSIMA_PRENOTAZIONE_MINUTI
            durata = int((fine - inizio).total_seconds() // 60)

            if durata < durata_min:
                raise forms.ValidationError(f"La durata minima della prenotazione è di {durata_min} minuti.")
            if durata > durata_max:
                raise forms.ValidationError(f"La durata massima della prenotazione è di {durata_max} minuti.")
            if fine <= inizio:
                raise forms.ValidationError("L'orario di fine deve essere successivo a quello di inizio.")

            # Controllo disponibilità
            from .services import BookingService
            is_available, disponibile, errors = BookingService.check_resource_availability(
                risorsa.id, inizio, fine, quantita, exclude_booking_id=self.prenotazione_id
            )

            if not is_available:
                raise forms.ValidationError(errors[0])

            # Salva dati puliti per uso successivo
            cleaned_data['inizio'] = inizio
            cleaned_data['fine'] = fine

        except ValueError:
            raise forms.ValidationError("Data o orario non validi.")

        return cleaned_data


class ConfirmDeleteForm(forms.Form):
    """
    Form di conferma per eliminazione prenotazione.
    """
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class AdminUserForm(forms.Form):
    """
    Form per la creazione del primo utente amministratore con verifica PIN via email.
    """
    from django.conf import settings

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label="Email amministratore",
        help_text=f"Email per la verifica PIN - deve essere del dominio @{settings.SCHOOL_EMAIL_DOMAIN}"
    )

    def clean_email(self):
        """Valida che l'email sia del dominio scolastico corretto e abbia il formato corretto."""
        import re
        email = self.cleaned_data['email']
        from django.conf import settings

        # Split email per controllare dominio
        try:
            local_part, domain_part = email.split('@')
        except ValueError:
            raise forms.ValidationError("Email non valida.")

        # Controlla dominio
        if domain_part.lower() != settings.SCHOOL_EMAIL_DOMAIN.lower():
            raise forms.ValidationError(
                f"Sono accettate solo email del dominio @{settings.SCHOOL_EMAIL_DOMAIN}. "
                f"Questo è necessario per garantire la sicurezza del sistema scolastico."
            )

        # Validate local-part: initial (letter), dot, full surname (letters, apostrophe allowed)
        # allow an optional numeric suffix after the surname (e.g. n.cantalupo1)
        # Note: apostrophe (') is allowed, hyphen is NOT
        local_regex = r"^[A-Za-z]\.[A-Za-zÀ-ÖØ-öø-ÿ']+[0-9]*$"
        if not re.match(local_regex, local_part):
            raise forms.ValidationError(
                "Formato email non valido. Esempi di indirizzi corretti: g.rossi@isufol.it o g.rossi1@isufol.it"
            )

        return email


class ConfigurazioneSistemaForm(forms.Form):
    """
    Form per la configurazione iniziale del sistema di prenotazioni.

    Passo 1: Numero di risorse da creare
    """
    num_risorse = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '20'
        }),
        label="Numero di risorse da configurare",
        help_text="Inserisci quante risorse vuoi creare (laboratori, carrelli, ecc.) - max 20"
    )


class RisorseConfigurazioneForm(forms.Form):
    """
    Form per il passo finale della configurazione risorse.

    Permette di selezionare dispositivi dai catalogati per creare carrelli.
    """

    def __init__(self, *args, **kwargs):
        self.num_risorse = kwargs.pop('num_risorse', None)
        self.dispositivi_disponibili = kwargs.pop('dispositivi_disponibili', None)
        super().__init__(*args, **kwargs)

        # Se abbiamo numero di risorse, aggiungiamo campi per ciascuna
        if self.num_risorse and self.dispositivi_disponibili is not None:
            dispositivi_choices = [(d.id, f"{d.produttore_display} {d.nome} ({d.modello})") for d in self.dispositivi_disponibili]

            for i in range(1, self.num_risorse + 1):
                # Campo nome - sempre visibile
                self.fields[f'nome_{i}'] = forms.CharField(
                    max_length=100,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'id': f'id_nome_{i}',
                        'placeholder': f'Es: Laboratorio {i}, Carrello Portatili {i}'
                    }),
                    label=f"Risorsa {i} - Nome",
                    help_text="Nome identificativo della risorsa (es: Lab Informatica, Carrello iPad)"
                )

                # Campo tipo - sempre visibile
                self.fields[f'tipo_{i}'] = forms.ChoiceField(
                    choices=Risorsa.TIPO_SCELTE,
                    widget=forms.Select(attrs={
                        'class': 'form-control',
                        'id': f'id_tipo_{i}',
                        'onchange': f'updateResourceFields({i})'
                    }),
                    label=f"Risorsa {i} - Tipo",
                    help_text="Seleziona il tipo di risorsa da creare"
                )

                # Campo selezione dispositivi - per carrelli
                self.fields[f'dispositivi_{i}'] = forms.MultipleChoiceField(
                    choices=dispositivi_choices,
                    widget=forms.SelectMultiple(attrs={
                        'class': 'form-control d-none',
                        'id': f'id_dispositivi_{i}',
                        'size': '4'
                    }),
                    label=f"Risorsa {i} - Dispositivi nel carrello",
                    help_text="Seleziona i dispositivi che saranno disponibili in questo carrello",
                    required=False
                )



    def clean(self):
        """
        Validazione personalizzata del form.
        """
        cleaned_data = super().clean()
        num_risorse = cleaned_data.get('num_risorse')

        if not num_risorse:
            return cleaned_data

        # Validiamo ogni risorsa
        for i in range(1, num_risorse + 1):
            nome = cleaned_data.get(f'nome_{i}')
            tipo = cleaned_data.get(f'tipo_{i}')

            if not nome or not tipo:
                continue

            # Per i carrelli, richiediamo la quantità
            if tipo == 'carrello':
                quantita = cleaned_data.get(f'quantita_{i}')
                if not quantita:
                    self.add_error(f'quantita_{i}', f"Specifica il numero di dispositivi per {nome}")
                elif quantita <= 0:
                    self.add_error(f'quantita_{i}', f"Il numero di dispositivi deve essere positivo")

        return cleaned_data


class DeviceWizardForm(forms.ModelForm):
    """
    Form semplificato per wizard configurazione sistemi - dispositivi.

    Campo active nascosto (sempre True per dispositivi di configurazione).
    """
    class Meta:
        model = Device
        fields = ['nome', 'tipo', 'produttore', 'modello', 'sistema_operativo',
                  'tipo_display', 'processore', 'storage', 'schermo', 'caratteristiche_extra']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'ej: iPad Pro 12.9'}),
            'produttore': forms.Select(attrs={'class': 'form-control mb-2'}),
            'modello': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'ej: A2343'}),
            'sistema_operativo': forms.Select(attrs={'class': 'form-control mb-2'}),
            'processore': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'ej: Apple M2, 8GB RAM'}),
            'storage': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'ej: 256GB SSD'}),
            'schermo': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'ej: 12.9" Liquid Retina XDR'}),
            'caratteristiche_extra': forms.Textarea(attrs={
                'class': 'form-control mb-2',
                'rows': 2,
                'placeholder': 'ej: Apple Pencil support, USB-C, etc.'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campo attivo non mostrato (sempre True nei wizard)
        if 'attivo' in self.fields:
            del self.fields['attivo']
        if 'tipo' in self.fields:
            del self.fields['tipo']  # Determinato automaticamente da produttore/sistema

    def clean(self):
        cleaned_data = super().clean()
        # Determina tipo automatico basato su produttore/sistema
        produttore = cleaned_data.get('produttore')
        sistema = cleaned_data.get('sistema_operativo')

        if produttore == 'apple' and sistema in ['ios', 'macos']:
            cleaned_data['tipo'] = 'notebook' if sistema == 'macos' else 'tablet'
        elif sistema == 'chromeos':
            cleaned_data['tipo'] = 'chromebook'
        elif sistema in ['windows', 'linux']:
            cleaned_data['tipo'] = 'notebook'
        elif sistema == 'android':
            cleaned_data['tipo'] = 'tablet'
        else:
            cleaned_data['tipo'] = 'altro'

        return cleaned_data


class DeviceForm(forms.ModelForm):
    """
    Form per creare/modificare dispositivi.
    """
    class Meta:
        model = Device
        fields = ['nome', 'tipo', 'produttore', 'modello', 'sistema_operativo',
                  'tipo_display', 'processore', 'storage', 'schermo', 'caratteristiche_extra']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'iPad Pro 12.9'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'produttore': forms.Select(attrs={'class': 'form-control'}),
            'modello': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A2343'}),
            'sistema_operativo': forms.Select(attrs={'class': 'form-control'}),
            'tipo_display': forms.Select(attrs={'class': 'form-control'}),
            'processore': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apple M2, 8GB RAM'
            }),
            'storage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '256GB SSD'
            }),
            'schermo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12.9" Liquid Retina XDR'
            }),
            'caratteristiche_extra': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Apple Pencil support, USB-C, etc.'
            }),
        }
        labels = {
            'nome': 'Nome commerciale',
            'tipo': 'Tipo dispositivo',
            'produttore': 'Produttore',
            'modello': 'Modello',
            'sistema_operativo': 'Sistema operativo',
            'tipo_display': 'Tipo display',
            'processore': 'CPU/RAM',
            'storage': 'Memoria',
            'schermo': 'Schermo',
            'caratteristiche_extra': 'Caratteristiche aggiuntive',
        }
        help_texts = {
            'nome': 'Nome commerciale del dispositivo (es. "iPad Pro 12.9")',
            'tipo': 'Categoria generale: notebook, tablet, chromebook',
            'produttore': 'Azienda produttrice (Apple, Dell, etc.)',
            'modello': 'Codice modello specifico',
            'sistema_operativo': 'OS installato sul dispositivo',
            'tipo_display': 'Tipo di display/interazione',
            'processore': 'CPU e quantità RAM (es. "Intel Core i5, 16GB RAM")',
            'storage': 'Capacità e tipo di storage (es. "512GB NVMe SSD")',
            'schermo': 'Dimensioni e caratteristiche display',
            'caratteristiche_extra': 'Porte, accessori, funzionalità speciali',
        }

    def clean(self):
        cleaned_data = super().clean()
        nome = cleaned_data.get('nome')
        modello = cleaned_data.get('modello')
        produttore = cleaned_data.get('produttore')

        # Controlla unicità nome + modello per produttore
        if nome and modello and produttore:
            qs = Device.objects.filter(
                nome=nome,
                modello=modello,
                produttore=produttore
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "Esiste già un dispositivo con questo nome, modello e produttore."
                )

        return cleaned_data


class SchoolInfoForm(forms.ModelForm):
    """
    Form per la configurazione delle informazioni sulla scuola.
    """
    class Meta:
        model = SchoolInfo
        fields = ['nome_scuola', 'codice_scuola', 'email_scuola', 'telefono', 'sito_web', 'indirizzo']
        widgets = {
            'nome_scuola': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo della scuola'}),
            'codice_scuola': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Codice meccanografico (es. ISUF001A)'}),
            'email_scuola': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'segreteria@scuola.it'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+39 0586 123456'}),
            'sito_web': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.scuola.edu.it'}),
            'indirizzo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Via Roma 123, 57128 Livorno (LI)'}),
        }
        labels = {
            'nome_scuola': 'Nome della scuola *',
            'codice_scuola': 'Codice meccanografico',
            'email_scuola': 'Email della scuola',
            'telefono': 'Telefono della scuola',
            'sito_web': 'Sito web della scuola',
            'indirizzo': 'Indirizzo completo',
        }
        help_texts = {
            'nome_scuola': 'Nome completo e ufficiale della scuola',
            'codice_scuola': 'Codice meccanografico identificativo della scuola',
            'email_scuola': 'Indirizzo email principale della scuola',
            'telefono': 'Numero di telefono della segreteria',
            'sito_web': 'URL del sito web istituzionale',
            'indirizzo': 'Indirizzo completo con CAP e provincia',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo nome_scuola è obbligatorio
        for field_name in self.fields:
            if field_name != 'nome_scuola':
                self.fields[field_name].required = False
