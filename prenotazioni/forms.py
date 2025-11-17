"""
Form Django per la validazione dei dati di prenotazione.
"""
from django import forms
from django.utils import timezone
from django.conf import settings
from .models import Prenotazione, Risorsa, SchoolInfo


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
            if quantita > risorsa.quantita_totale:
                raise forms.ValidationError(f"Quantità richiesta ({quantita}) supera la disponibilità totale ({risorsa.quantita_totale}).")

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
        """Valida che l'email sia del dominio scolastico corretto."""
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

        return email


class ConfigurazioneSistemaForm(forms.Form):
    """
    Form per la configurazione iniziale del sistema di prenotazioni.

    Permette di creare dinamicamente risorse (laboratori e carrelli).
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

    def __init__(self, *args, **kwargs):
        self.num_risorse = kwargs.pop('num_risorse', None)
        super().__init__(*args, **kwargs)

        # Se abbiamo numero di risorse, aggiungiamo camp i per ciascuna
        if self.num_risorse:
            for i in range(1, self.num_risorse + 1):
                # Campo nome - sempre visibile
                self.fields[f'nome_{i}'] = forms.CharField(
                    max_length=120,
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

                # Campo quantità - condizionale per carrelli
                self.fields[f'quantita_{i}'] = forms.IntegerField(
                    min_value=1,
                    max_value=100,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control d-none',
                        'id': f'id_quantita_{i}',
                        'min': '1',
                        'max': '100',
                        'placeholder': 'Es: 30 dispositivi'
                    }),
                    label=f"Risorsa {i} - Numero dispositivi",
                    help_text="Quanti dispositivi contiene questo carrello?",
                    required=False
                )

                # Campo selezione dispositivi - condizionale per carrelli
                self.fields[f'dispositivi_{i}'] = forms.MultipleChoiceField(
                    choices=[],  # Sarà popolato dinamicamente
                    widget=forms.SelectMultiple(attrs={
                        'class': 'form-control d-none',
                        'id': f'id_dispositivi_{i}',
                        'size': '4'
                    }),
                    label=f"Risorsa {i} - Dispositivi contenuti",
                    help_text="Seleziona i dispositivi che contiene questo carrello (puoi crearne di nuovi sotto)",
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


class DeviceForm(forms.ModelForm):
    """
    Form per creare/modificare dispositivi.
    """
    class Meta:
        model = Device
        fields = ['nome', 'tipo', 'modello', 'caratteristiche']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'iPad Pro 11", MacBook Air M2'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'modello': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'M2, M1, 2023'}),
            'caratteristiche': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'CPU: Apple M2, RAM: 8GB, Storage: 256GB, Display: 13.6"'
            }),
        }
        labels = {
            'nome': 'Nome dispositivo',
            'tipo': 'Tipo',
            'modello': 'Modello',
            'caratteristiche': 'Caratteristiche tecniche',
        }


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
