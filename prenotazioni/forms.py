"""
Form Django per la nuova architettura del sistema di prenotazioni.

Aggiornati per supportare la nuova struttura database migliorata.
"""

from django import forms
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import (
    Risorsa, Dispositivo, Prenotazione, ConfigurazioneSistema,
    ProfiloUtente, InformazioniScuola, SessioneUtente, StatoPrenotazione,
    UbicazioneRisorsa, CategoriaDispositivo, TemplateNotifica, CaricamentoFile
)

User = get_user_model()


# =====================================================
# CONFIGURAZIONE E SETUP
# =====================================================

class ConfigurationForm(forms.ModelForm):
    """Form per gestire configurazioni di sistema."""

    class Meta:
        model = ConfigurazioneSistema
        fields = ['chiave', 'valore', 'tipo', 'descrizione', 'modificabile']
        widgets = {
            'chiave': forms.TextInput(attrs={'class': 'form-control'}),
            'valore': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'modificabile': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'chiave': 'Chiave',
            'valore': 'Valore',
            'tipo': 'Tipo',
            'descrizione': 'Descrizione',
            'modificabile': 'Modificabile',
        }

    def clean_chiave(self):
        chiave = self.cleaned_data['chiave'].upper()
        # Validazione formato chiave (solo lettere, numeri, underscore)
        if not chiave.replace('_', '').isalnum():
            raise ValidationError("La chiave può contenere solo lettere, numeri e underscore.")
        return chiave


class SchoolInfoForm(forms.ModelForm):
    """Form per informazioni complete della scuola."""
    
    class Meta:
        model = SchoolInfo
        fields = [
            'nome_completo', 'nome_breve', 'codice_meccanografico', 'partita_iva',
            'sito_web', 'email_istituzionale', 'telefono', 'fax',
            'indirizzo', 'cap', 'comune', 'provincia', 'regione', 'nazione',
            'latitudine', 'longitudine'
        ]
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_breve': forms.TextInput(attrs={'class': 'form-control'}),
            'codice_meccanografico': forms.TextInput(attrs={'class': 'form-control'}),
            'partita_iva': forms.TextInput(attrs={'class': 'form-control'}),
            'sito_web': forms.URLInput(attrs={'class': 'form-control'}),
            'email_istituzionale': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'indirizzo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cap': forms.TextInput(attrs={'class': 'form-control'}),
            'comune': forms.TextInput(attrs={'class': 'form-control'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control'}),
            'regione': forms.TextInput(attrs={'class': 'form-control'}),
            'nazione': forms.TextInput(attrs={'class': 'form-control'}),
            'latitudine': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000001'}),
            'longitudine': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000001'}),
        }

    def clean_codice_meccanografico(self):
        codice = self.cleaned_data['codice_meccanografico'].upper()
        if len(codice) != 10:
            raise ValidationError("Il codice meccanografico deve essere di esattamente 10 caratteri.")
        return codice


# =====================================================
# GESTIONE UTENTI
# =====================================================

class UserProfileForm(forms.ModelForm):
    """Form per profilo utente esteso."""
    
    class Meta:
        model = UserProfile
        fields = [
            'nome', 'cognome', 'sesso', 'data_nascita', 'codice_fiscale',
            'telefono', 'email_personale', 'numero_matricola', 'classe',
            'dipartimento', 'materia_insegnamento', 'preferenze_notifica',
            'preferenze_lingua', 'fuso_orario'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cognome': forms.TextInput(attrs={'class': 'form-control'}),
            'sesso': forms.Select(attrs={'class': 'form-select'}),
            'data_nascita': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'codice_fiscale': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email_personale': forms.EmailInput(attrs={'class': 'form-control'}),
            'numero_matricola': forms.TextInput(attrs={'class': 'form-control'}),
            'classe': forms.TextInput(attrs={'class': 'form-control'}),
            'dipartimento': forms.TextInput(attrs={'class': 'form-control'}),
            'materia_insegnamento': forms.TextInput(attrs={'class': 'form-control'}),
            'preferenze_notifica': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preferenze_lingua': forms.Select(attrs={'class': 'form-select'}),
            'fuso_orario': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_codice_fiscale(self):
        cf = self.cleaned_data['codice_fiscale'].upper()
        if cf and len(cf) != 16:
            raise ValidationError("Il codice fiscale deve essere di 16 caratteri.")
        return cf


class UtenteForm(forms.ModelForm):
    """Form per utente di sistema."""

    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Conferma Password'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Le password non coincidono.")
        
        return cleaned_data


class AdminUserForm(forms.Form):
    """Form per creazione primo utente amministratore."""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label="Email amministratore",
        help_text=f"Email per la verifica PIN - deve essere del dominio @{settings.SCHOOL_EMAIL_DOMAIN if hasattr(settings, 'SCHOOL_EMAIL_DOMAIN') else 'isufol.it'}"
    )
    
    nome = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Nome"
    )
    
    cognome = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Cognome"
    )

    def clean_email(self):
        """Validazione email formato istituzionale."""
        import re
        email = self.cleaned_data['email']
        domain = getattr(settings, 'SCHOOL_EMAIL_DOMAIN', 'isufol.it')
        
        try:
            local_part, domain_part = email.split('@')
        except ValueError:
            raise ValidationError("Email non valida.")
        
        if domain_part.lower() != domain.lower():
            raise ValidationError(
                f"Sono accettate solo email del dominio @{domain}."
            )
        
        # Validazione formato: iniziale.cognome[optional_number]
        local_regex = r"^[A-Za-z]\.[A-Za-zÀ-ÖØ-öø-ÿ']+[0-9]*$"
        if not re.match(local_regex, local_part):
            raise ValidationError(
                "Formato email non valido. Esempi: g.rossi@isufol.it o g.rossi1@isufol.it"
            )
        
        return email


# =====================================================
# GESTIONE SESSIONI E VERIFICHE
# =====================================================

class UserSessionForm(forms.ModelForm):
    """Form per gestione sessioni utente."""
    
    class Meta:
        model = UserSession
        fields = ['tipo', 'metadata', 'email_destinazione']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'metadata': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email_destinazione': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class PinVerificationForm(forms.Form):
    """Form per verifica PIN."""
    
    pin = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Inserisci PIN a 6 cifre',
            'style': 'text-align: center; font-size: 18px; letter-spacing: 0.5rem;'
        }),
        label='PIN di Verifica'
    )


class EmailLoginForm(forms.Form):
    """Form per login tramite email."""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'i.cognome@isufol.it'
        }),
        label='Email Istituzionale'
    )


# =====================================================
# CATALOGO DISPOSITIVI
# =====================================================

class DeviceCategoryForm(forms.ModelForm):
    """Form per categorie dispositivi."""
    
    class Meta:
        model = DeviceCategory
        fields = ['nome', 'descrizione', 'icona', 'colore', 'ordine']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'icona': forms.TextInput(attrs={'class': 'form-control'}),
            'colore': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'ordine': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class DeviceForm(forms.ModelForm):
    """Form per dispositivi con campi estesi."""
    
    class Meta:
        model = Device
        fields = [
            'nome', 'modello', 'marca', 'serie', 'codice_inventario', 'tipo',
            'categoria', 'specifiche', 'stato', 'edificio', 'piano', 'aula', 'armadio',
            'data_acquisto', 'data_scadenza_garanzia', 'valore_acquisto', 'note',
            'ultimo_controllo', 'prossima_manutenzione'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'modello': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'serie': forms.TextInput(attrs={'class': 'form-control'}),
            'codice_inventario': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'specifiche': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'stato': forms.Select(attrs={'class': 'form-select'}),
            'edificio': forms.TextInput(attrs={'class': 'form-control'}),
            'piano': forms.TextInput(attrs={'class': 'form-control'}),
            'aula': forms.TextInput(attrs={'class': 'form-control'}),
            'armadio': forms.TextInput(attrs={'class': 'form-control'}),
            'data_acquisto': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_scadenza_garanzia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valore_acquisto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ultimo_controllo': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'prossima_manutenzione': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class DeviceWizardForm(forms.ModelForm):
    """Form semplificato per wizard configurazione."""
    
    class Meta:
        model = Device
        fields = ['nome', 'tipo', 'marca', 'modello', 'categoria']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'es: iPad Pro 12.9'}),
            'tipo': forms.Select(attrs={'class': 'form-control mb-2'}),
            'marca': forms.TextInput(attrs={'class': 'form-control mb-2'}),
            'modello': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'es: A2343'}),
            'categoria': forms.Select(attrs={'class': 'form-control mb-2'}),
        }


# =====================================================
# RISORSE E LOCALIZZAZIONI
# =====================================================

class ResourceLocationForm(forms.ModelForm):
    """Form per localizzazioni."""
    
    class Meta:
        model = ResourceLocation
        fields = ['nome', 'descrizione', 'edificio', 'piano', 'aula', 'capacita_persone']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'edificio': forms.TextInput(attrs={'class': 'form-control'}),
            'piano': forms.TextInput(attrs={'class': 'form-control'}),
            'aula': forms.TextInput(attrs={'class': 'form-control'}),
            'capacita_persone': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ResourceForm(forms.ModelForm):
    """Form per risorse prenotabili."""
    
    # Orari apertura JSON field helper
    orari_personalizzati = forms.JSONField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Orari personalizzati della risorsa"
    )
    
    class Meta:
        model = Resource
        fields = [
            'nome', 'codice', 'descrizione', 'tipo', 'categoria', 'localizzazione',
            'capacita_massima', 'postazioni_disponibili', 'feriali_disponibile',
            'weekend_disponibile', 'festivo_disponibile', 'attivo', 'manutenzione',
            'bloccato', 'prenotazione_anticipo_minimo', 'prenotazione_anticipo_massimo',
            'durata_minima_minuti', 'durata_massima_minuti', 'allow_overbooking',
            'overbooking_limite', 'note_amministrative', 'note_utenti'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codice': forms.TextInput(attrs={'class': 'form-control'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control'}),
            'localizzazione': forms.Select(attrs={'class': 'form-select'}),
            'capacita_massima': forms.NumberInput(attrs={'class': 'form-control'}),
            'postazioni_disponibili': forms.NumberInput(attrs={'class': 'form-control'}),
            'feriali_disponibile': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'weekend_disponibile': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'festivo_disponibile': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'manutenzione': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bloccato': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prenotazione_anticipo_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'prenotazione_anticipo_massimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'durata_minima_minuti': forms.NumberInput(attrs={'class': 'form-control'}),
            'durata_massima_minuti': forms.NumberInput(attrs={'class': 'form-control'}),
            'allow_overbooking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'overbooking_limite': forms.NumberInput(attrs={'class': 'form-control'}),
            'note_amministrative': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'note_utenti': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RisorseConfigurazioneForm(forms.Form):
    """Form per configurazione risorse durante setup."""
    
    def __init__(self, *args, **kwargs):
        num_risorse = kwargs.pop('num_risorse', None)
        dispositivi_disponibili = kwargs.pop('dispositivi_disponibili', None)
        super().__init__(*args, **kwargs)
        
        if num_risorse and dispositivi_disponibili:
            dispositivi_choices = [(d.id, d.display_name) for d in dispositivi_disponibili]
            
            for i in range(1, num_risorse + 1):
                self.fields[f'nome_{i}'] = forms.CharField(
                    max_length=100,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': f'Es: Laboratorio {i}, Carrello {i}'
                    }),
                    label=f"Risorsa {i} - Nome"
                )
                
                self.fields[f'tipo_{i}'] = forms.ChoiceField(
                    choices=Resource.TIPO_RISORSA,
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    label=f"Risorsa {i} - Tipo"
                )
                
                self.fields[f'dispositivi_{i}'] = forms.MultipleChoiceField(
                    choices=dispositivi_choices,
                    widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'}),
                    label=f"Risorsa {i} - Dispositivi",
                    required=False
                )


# =====================================================
# PRENOTAZIONI
# =====================================================

class BookingStatusForm(forms.ModelForm):
    """Form per stati prenotazione."""
    
    class Meta:
        model = BookingStatus
        fields = ['nome', 'descrizione', 'colore', 'icon', 'ordine']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'colore': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'ordine': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class BookingForm(forms.Form):
    """Form principale per prenotazioni."""
    
    RISORSA_CHOICES = []  # Popolato dinamicamente
    
    risorsa = forms.ModelChoiceField(
        queryset=Resource.objects.none(),
        empty_label="Seleziona una risorsa",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_risorsa'})
    )
    
    data = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': timezone.now().date().isoformat()
        })
    )
    
    ora_inizio = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    ora_fine = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    quantita = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )
    
    scopo = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    priorita = forms.ChoiceField(
        choices=Booking.PRIORITA,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='normale'
    )
    
    setup_needed = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Richiede assistenza tecnica per il setup"
    )
    
    cleanup_needed = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Richiede assistenza per il riordino"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.prenotazione_id = kwargs.pop('prenotazione_id', None)
        super().__init__(*args, **kwargs)
        
        # Filtra risorse disponibili
        self.fields['risorsa'].queryset = Resource.objects.filter(
            attivo=True, manutenzione=False, bloccato=False
        ).order_by('tipo', 'nome')
    
    def clean(self):
        """Validazione completa del form."""
        cleaned_data = super().clean()
        risorsa = cleaned_data.get('risorsa')
        data = cleaned_data.get('data')
        ora_inizio = cleaned_data.get('ora_inizio')
        ora_fine = cleaned_data.get('ora_fine')
        quantita = cleaned_data.get('quantita')
        
        if not all([risorsa, data, ora_inizio, ora_fine, quantita]):
            return cleaned_data
        
        # Validazione orari
        if ora_inizio >= ora_fine:
            raise ValidationError("L'orario di fine deve essere successivo a quello di inizio.")
        
        # Validazione orari consentiti (configurabili)
        configuration_start = getattr(settings, 'BOOKING_START_HOUR', '08:00')
        configuration_end = getattr(settings, 'BOOKING_END_HOUR', '18:00')
        
        ora_inizio_str = ora_inizio.strftime('%H:%M')
        ora_fine_str = ora_fine.strftime('%H:%M')
        
        if ora_inizio_str < configuration_start or ora_fine_str > configuration_end:
            raise ValidationError(
                f"Le prenotazioni sono consentite solo tra le {configuration_start} e le {configuration_end}."
            )
        
        # Validazione durata
        try:
            inizio_dt = timezone.datetime.combine(data, ora_inizio)
            fine_dt = timezone.datetime.combine(data, ora_fine)
            inizio_dt = timezone.make_aware(inizio_dt)
            fine_dt = timezone.make_aware(fine_dt)
            
            durata_minuti = int((fine_dt - inizio_dt).total_seconds() // 60)
            
            durata_min_config = getattr(settings, 'DURATA_MINIMA_PRENOTAZIONE_MINUTI', 30)
            durata_max_config = getattr(settings, 'DURATA_MASSIMA_PRENOTAZIONE_MINUTI', 180)
            
            if durata_minuti < durata_min_config:
                raise ValidationError(f"La durata minima è di {durata_min_config} minuti.")
            if durata_minuti > durata_max_config:
                raise ValidationError(f"La durata massima è di {durata_max_config} minuti.")
            
            # Validazione anticipo
            giorni_anticipo = getattr(settings, 'GIORNI_ANTICIPO_PRENOTAZIONE', 2)
            if (data - timezone.now().date()).days < giorni_anticipo:
                raise ValidationError(f"La prenotazione deve essere fatta almeno {giorni_anticipo} giorni prima.")
            
            # Validazione disponibilità
            from .services import BookingService
            is_available, disponibile, errors = BookingService.check_resource_availability(
                risorsa.id, inizio_dt, fine_dt, quantita, exclude_booking_id=self.prenotazione_id
            )
            
            if not is_available:
                raise ValidationError(errors[0] if errors else "Risorsa non disponibile.")
            
            # Salva datetime per uso successivo
            cleaned_data['inizio'] = inizio_dt
            cleaned_data['fine'] = fine_dt
            
        except ValueError as e:
            raise ValidationError(f"Errore nei dati temporali: {e}")
        
        return cleaned_data


class ConfirmDeleteForm(forms.Form):
    """Form di conferma per eliminazione."""
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Confermo di voler eliminare questa prenotazione"
    )


# =====================================================
# SISTEMA DI LOG E MONITORAGGIO
# =====================================================

class SystemLogForm(forms.ModelForm):
    """Form per visualizzazione/log sistema."""
    
    class Meta:
        model = None  # SistemaLog è read-only per utenti normali
        exclude = []


class NotificationTemplateForm(forms.ModelForm):
    """Form per template notifiche."""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'nome', 'tipo', 'evento', 'oggetto', 'contenuto', 'attivo',
            'invio_immediato', 'tentativi_massimi', 'intervallo_tentativi_minuti'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'evento': forms.TextInput(attrs={'class': 'form-control'}),
            'oggetto': forms.TextInput(attrs={'class': 'form-control'}),
            'contenuto': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'invio_immediato': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tentativi_massimi': forms.NumberInput(attrs={'class': 'form-control'}),
            'intervallo_tentativi_minuti': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# =====================================================
# FILE E ALLEGATI
# =====================================================

class FileUploadForm(forms.ModelForm):
    """Form per caricamento file."""
    
    class Meta:
        model = FileUpload
        fields = ['file', 'titolo', 'descrizione', 'tags', 'pubblico']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'titolo': forms.TextInput(attrs={'class': 'form-control'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
            'pubblico': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'tags': 'Inserire i tag separati da virgola',
        }

    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            # Validazione dimensione (10MB max)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("Il file è troppo grande (max 10MB).")
            
            # Validazione tipo MIME
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif',
                'application/pdf', 'text/plain',
                'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            if file.content_type not in allowed_types:
                raise ValidationError("Tipo di file non supportato.")
        
        return file


# =====================================================
# FORM WIZARD CONFIGURAZIONE
# =====================================================

class ConfigurazioneSistemaForm(forms.Form):
    """Form per numero risorse da configurare."""
    
    num_risorse = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '20'
        }),
        label="Numero di risorse da configurare"
    )
