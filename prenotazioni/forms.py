"""
Form Django per la nuova architettura del sistema di prenotazioni.

Aggiornati per supportare la nuova struttura database migliorata.
"""


from django import forms
from django.utils import timezone
from django.conf import settings
import uuid
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_protect
from .models import (
    InformazioniScuola,
    CategoriaDispositivo as DeviceCategory,
    Dispositivo as Device,
    UbicazioneRisorsa as ResourceLocation,
    Risorsa as Resource,
    StatoPrenotazione as BookingStatus,
    Prenotazione as Booking,
    ConfigurazioneSistema,
    TemplateNotifica as NotificationTemplate,
    CaricamentoFile as FileUpload,
    LogSistema as SystemLog,
)


class InformazioniScuolaForm(forms.ModelForm):
    class Meta:
        model = InformazioniScuola
        fields = [
            'nome_completo_scuola', 'codice_meccanografico_scuola',
            'partita_iva_scuola', 'sito_web_scuola', 'email_istituzionale_scuola',
            'telefono_scuola', 'indirizzo_scuola', 'codice_postale_scuola',
            'comune_scuola', 'provincia_scuola', 'regione_scuola', 'nazione_scuola',
            'scuola_attiva'
        ]
        widgets = {
            'nome_completo_scuola': forms.TextInput(attrs={'class': 'form-control'}),
            'codice_meccanografico_scuola': forms.TextInput(attrs={'class': 'form-control'}),
            'partita_iva_scuola': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Non disponibile nel dataset ufficiale - inserire manualmente'}),
            'telefono_scuola': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Non disponibile nel dataset ufficiale - inserire manualmente'}),
            'sito_web_scuola': forms.URLInput(attrs={'class': 'form-control'}),
            'email_istituzionale_scuola': forms.EmailInput(attrs={'class': 'form-control'}),
            'indirizzo_scuola': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_indirizzo_autocomplete'}),
            'codice_postale_scuola': forms.TextInput(attrs={'class': 'form-control'}),
            'comune_scuola': forms.TextInput(attrs={'class': 'form-control'}),
            'provincia_scuola': forms.TextInput(attrs={'class': 'form-control'}),
            'regione_scuola': forms.TextInput(attrs={'class': 'form-control'}),
            'nazione_scuola': forms.TextInput(attrs={'class': 'form-control'}),
            'scuola_attiva': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_codice_meccanografico_scuola(self):
        codice = self.cleaned_data.get('codice_meccanografico_scuola')
        if not codice:
            return ''
        codice = codice.upper()
        if len(codice) != 10:
            raise ValidationError("Il codice meccanografico deve essere di esattamente 10 caratteri.")
        return codice

    def clean_sito_web_scuola(self):
        sito = self.cleaned_data.get('sito_web_scuola')
        if not sito:
            return ''
        # Normalize: allow values like 'www.example.edu.it' by prepending https://
        try:
            from urllib.parse import urlparse
            sito_to_parse = sito
            if not sito_to_parse.lower().startswith(('http://', 'https://')):
                sito_to_parse = 'https://' + sito_to_parse
            parsed = urlparse(sito_to_parse)
            hostname = parsed.hostname or ''
        except Exception:
            raise ValidationError('URL non valido.')

        if not hostname.lower().endswith('edu.it'):
            raise ValidationError('Il sito web della scuola deve appartenere al dominio *.edu.it')

        # Return normalized URL including scheme so stored value is valid
        return sito_to_parse

    def clean_indirizzo_scuola(self):
        """Validazione semplice per l'indirizzo scuola: non può essere vuoto.

        Il campo viene compilato dall'autocomplete client-side quando possibile.
        Lato server accettiamo qualsiasi stringa non vuota per permettere
        all'utente di proseguire anche se la lat/long non sono state impostate.
        """
        import json
        from urllib import parse, request

        indirizzo = self.cleaned_data.get('indirizzo_scuola', '')
        if not indirizzo or not str(indirizzo).strip():
            raise ValidationError("Questo campo non può essere nullo.")

        # Require client to submit OSM identifiers from the autocomplete
        osm_id = (self.data.get('osm_id_scuola') or '').strip()
        osm_type = (self.data.get('osm_type_scuola') or '').strip()

        # Allow addresses coming from the CSV lookup: client will set osm_type='csv' and osm_id='csv_<codice>'
        if osm_type.lower().startswith('csv') and osm_id:
            # Accept CSV-provided address without contacting Nominatim.
            # Use values populated client-side (lat/lon, address components) and return.
            lat = self.cleaned_data.get('latitudine_scuola')
            lon = self.cleaned_data.get('longitudine_scuola')
            try:
                self.cleaned_data['latitudine_scuola'] = float(lat) if lat else None
                self.cleaned_data['longitudine_scuola'] = float(lon) if lon else None
            except Exception:
                self.cleaned_data['latitudine_scuola'] = None
                self.cleaned_data['longitudine_scuola'] = None

            # Copy address components if present
            cap = self.cleaned_data.get('codice_postale_scuola', '')
            comune = self.cleaned_data.get('comune_scuola', '')
            provincia = self.cleaned_data.get('provincia_scuola', '')
            regione = self.cleaned_data.get('regione_scuola', '')
            nazione = self.cleaned_data.get('nazione_scuola', '')

            self.cleaned_data['codice_postale_scuola'] = cap
            self.cleaned_data['comune_scuola'] = comune
            self.cleaned_data['provincia_scuola'] = provincia
            self.cleaned_data['regione_scuola'] = regione
            self.cleaned_data['nazione_scuola'] = nazione

            formatted = self.cleaned_data.get('indirizzo_scuola') or str(indirizzo).strip()
            return formatted

        if not osm_id or not osm_type:
            raise ValidationError("Seleziona un suggerimento valido dall'elenco (scegli la scuola).")

        # Map osm_type to lookup prefix
        type_map = {'node': 'N', 'way': 'W', 'relation': 'R', 'n': 'N', 'w': 'W', 'r': 'R'}
        osm_letter = type_map.get(osm_type.lower())
        if not osm_letter:
            raise ValidationError("Tipo OSM non valido fornito.")

        lookup_url = 'https://nominatim.openstreetmap.org/lookup'
        params = {
            'osm_ids': f"{osm_letter}{osm_id}",
            'format': 'jsonv2',
            'addressdetails': 1,
            'extratags': 1
        }

        full_url = lookup_url + '?' + parse.urlencode(params)
        try:
            req = request.Request(full_url, headers={'User-Agent': 'prenotazioni-scuola-project'})
            with request.urlopen(req, timeout=10) as resp:
                body = resp.read()
                data = json.loads(body.decode('utf-8'))
        except Exception as e:
            raise ValidationError(f"Errore contattando Nominatim (OpenStreetMap): {e}")

        if not isinstance(data, list) or len(data) == 0:
            raise ValidationError("Nessun risultato trovato per il luogo selezionato.")

        result = data[0]

        # Heuristics to ensure the selected place is a school
        is_school = False
        cls = (result.get('class') or '').lower()
        typ = (result.get('type') or '').lower()
        extratags = result.get('extratags') or {}
        if cls == 'amenity' and typ in ('school', 'college', 'university'):
            is_school = True
        amenity_tag = (extratags.get('amenity') or '').lower()
        if amenity_tag in ('school', 'college', 'university'):
            is_school = True
        if not is_school:
            display = (result.get('display_name') or '').lower()
            if any(k in display for k in ('scuola', 'istituto', 'liceo', 'istituto tecnico')):
                is_school = True

        if not is_school:
            raise ValidationError("Devi selezionare un luogo che sia una scuola (seleziona la scuola dall'elenco).")

        lat = result.get('lat')
        lon = result.get('lon')
        address = result.get('address') or {}

        cap = address.get('postcode', '')
        comune = address.get('city') or address.get('town') or address.get('village') or ''
        provincia = address.get('county') or address.get('state_district') or ''
        if provincia and provincia.lower().startswith('provincia di '):
            provincia = provincia[12:]
        regione = address.get('state') or ''
        nazione = address.get('country') or ''

        try:
            self.cleaned_data['latitudine_scuola'] = float(lat) if lat else None
            self.cleaned_data['longitudine_scuola'] = float(lon) if lon else None
        except Exception:
            self.cleaned_data['latitudine_scuola'] = None
            self.cleaned_data['longitudine_scuola'] = None

        self.cleaned_data['codice_postale_scuola'] = cap
        self.cleaned_data['comune_scuola'] = comune
        self.cleaned_data['provincia_scuola'] = provincia
        self.cleaned_data['regione_scuola'] = regione
        self.cleaned_data['nazione_scuola'] = nazione

        formatted = result.get('display_name') or str(indirizzo).strip()
        return formatted


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
    """Form per login tramite email.
    
    La validazione del formato/dominio email verrà implementata
    durante lo step di configurazione del sistema per adattarsi
    alle specifiche esigenze dell'istituto.
    """
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'nome.cognome@dominio.it'
        }),
        label='Email Istituzionale',
        help_text='Inserisci la tua email scolastica'
    )


# Backwards-compatible aliases / additional simple forms expected by views
class AdminUserForm(forms.Form):
    """Form per collezionare email primo utente che diventerà amministratore.
    
    IMPORTANTE:
    - Il primo utente che accede al sistema diventerà AUTOMATICAMENTE amministratore
    - Questo ruolo NON POTRÀ ESSERE CAMBIATO IN SEGUITO
    - L'email può essere un indirizzo personale (qualsiasi dominio)
    - La validazione è solo sul formato email (non sul dominio)
    
    Successivamente gli altri utenti (docenti con email scolastica) dovranno
    rispettare il formato e dominio configurati dall'istituto.
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin@example.com'
        }),
        label='Email Amministratore',
        help_text='Può essere un indirizzo email personale (qualsiasi dominio)'
    )
    
    def clean_email(self):
        """Valida che l'email abbia un formato corretto.
        
        NOTE:
        - Qualsiasi dominio è accettato (non solo .edu.it)
        - La validazione del dominio per gli altri utenti sarà
          configurata in uno step successivo
        """
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise ValidationError('Questo campo non può essere vuoto.')
        
        # Semplice validazione: assicura che sia un'email valida
        # Django già valida il formato tramite EmailField
        # Qui non facciamo controlli sul dominio
        
        return email.lower()


class ConfigurationForm(forms.ModelForm):
    """ModelForm wrapper for `ConfigurazioneSistema` expected by admin views."""
    class Meta:
        model = ConfigurazioneSistema
        fields = [
            'chiave_configurazione', 'valore_configurazione', 'tipo_configurazione',
            'descrizione_configurazione', 'configurazione_modificabile'
        ]
        widgets = {
            'chiave_configurazione': forms.TextInput(attrs={'class': 'form-control'}),
            'valore_configurazione': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo_configurazione': forms.Select(attrs={'class': 'form-select'}),
            'descrizione_configurazione': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'configurazione_modificabile': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


# Alias expected by older view imports
SchoolInfoForm = InformazioniScuolaForm


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
            'categoria', 'ubicazione', 'specifiche', 'stato',
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
            'ubicazione': forms.Select(attrs={'class': 'form-select'}),
            'specifiche': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'stato': forms.Select(attrs={'class': 'form-select'}),
            'data_acquisto': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_scadenza_garanzia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valore_acquisto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ultimo_controllo': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'prossima_manutenzione': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class DeviceWizardForm(forms.ModelForm):
    """Form semplificato per wizard configurazione."""
    
    # Campo ubicazione richiesto per FK a UbicazioneRisorsa
    ubicazione = forms.ModelChoiceField(
        queryset=ResourceLocation.objects.all(),
        label='Ubicazione Dispositivo',
        empty_label='-- Seleziona ubicazione --',
        widget=forms.Select(attrs={'class': 'form-control mb-2'}),
        help_text='Dove si trova fisicamente il dispositivo'
    )
    
    class Meta:
        model = Device
        fields = ['nome', 'tipo', 'marca', 'modello', 'categoria', 'ubicazione']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'es: iPad Pro 12.9'}),
            'tipo': forms.Select(attrs={'class': 'form-control mb-2'}),
            'marca': forms.TextInput(attrs={'class': 'form-control mb-2'}),
            'modello': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'es: A2343'}),
            'categoria': forms.Select(attrs={'class': 'form-control mb-2'}),
        }

    def save(self, commit=True):
        """Override save to ensure required fields on the model are populated.

        The wizard form intentionally exposes a simplified subset of fields.
        The `Dispositivo` model requires `codice_inventario` (unique, non-null),
        so we auto-generate a deterministic inventory code when missing.
        """
        instance = super().save(commit=False)
        # Ensure codice_inventario exists (model requires it)
        if not getattr(instance, 'codice_inventario', None):
            instance.codice_inventario = 'AUTO-' + uuid.uuid4().hex[:8].upper()

        if commit:
            instance.save()
            try:
                self.save_m2m()
            except Exception:
                # save_m2m may fail if not using a ModelForm with many-to-many
                pass

        return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the ubicazione queryset is always fresh at form instantiation time
        try:
            self.fields['ubicazione'].queryset = ResourceLocation.objects.all()
        except Exception:
            # If ResourceLocation model isn't available or field missing, ignore
            pass


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
            'nome', 'tipo', 'evento', 'oggetto', 'contenuto', 'attivo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'evento': forms.TextInput(attrs={'class': 'form-control'}),
            'oggetto': forms.TextInput(attrs={'class': 'form-control'}),
            'contenuto': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
