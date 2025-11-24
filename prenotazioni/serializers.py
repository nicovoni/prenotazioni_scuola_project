"""
Serializers Django REST Framework riallineati ai modelli attuali.

Ho mantenuto i serializer principali (risorse, dispositivi, prenotazioni,
sessioni, configurazione e notifiche) e ho aggiornato i nomi dei campi
per usare i nomi effettivi dei modelli.
"""

from rest_framework import serializers
import logging
from django.contrib.auth import get_user_model

from .models import (
    Risorsa, Dispositivo, Prenotazione, ConfigurazioneSistema, SessioneUtente,
    LogSistema, TemplateNotifica, NotificaUtente, ProfiloUtente,
    UbicazioneRisorsa, CategoriaDispositivo, StatoPrenotazione, CaricamentoFile, InformazioniScuola
)

User = get_user_model()


class ConfigurationSerializer(serializers.ModelSerializer):
    # Compatibility aliases expected by some frontends
    chiave = serializers.CharField(source='chiave_configurazione', read_only=True)
    valore = serializers.CharField(source='valore_configurazione', read_only=True)
    tipo = serializers.CharField(source='tipo_configurazione', read_only=True)
    descrizione = serializers.CharField(source='descrizione_configurazione', read_only=True)
    modificabile = serializers.BooleanField(source='configurazione_modificabile', read_only=True)
    class Meta:
        model = ConfigurazioneSistema
        fields = [
            'id', 'chiave_configurazione', 'valore_configurazione', 'tipo_configurazione',
            'descrizione_configurazione', 'configurazione_modificabile',
            'data_creazione_configurazione', 'data_modifica_configurazione'
        ]
        read_only_fields = ['id', 'data_creazione_configurazione', 'data_modifica_configurazione']


class SchoolInfoSerializer(serializers.ModelSerializer):
    indirizzo_completo_scuola = serializers.CharField(read_only=True)
    # Short alias fields for compatibility
    nome_completo = serializers.CharField(source='nome_completo_scuola', read_only=True)
    nome_breve = serializers.CharField(source='nome_breve_scuola', read_only=True)
    codice_meccanografico = serializers.CharField(source='codice_meccanografico_scuola', read_only=True)
    partita_iva = serializers.CharField(source='partita_iva_scuola', read_only=True)
    email_istituzionale = serializers.CharField(source='email_istituzionale_scuola', read_only=True)
    indirizzo = serializers.CharField(source='indirizzo_scuola', read_only=True)
    cap = serializers.CharField(source='codice_postale_scuola', read_only=True)
    comune = serializers.CharField(source='comune_scuola', read_only=True)
    provincia = serializers.CharField(source='provincia_scuola', read_only=True)
    regione = serializers.CharField(source='regione_scuola', read_only=True)

    class Meta:
        model = InformazioniScuola
        fields = [
            'id', 'nome_completo_scuola', 'nome_breve_scuola', 'codice_meccanografico_scuola',
            'partita_iva_scuola', 'sito_web_scuola', 'email_istituzionale_scuola', 'telefono_scuola',
            'fax_scuola', 'indirizzo_scuola', 'codice_postale_scuola', 'comune_scuola', 'provincia_scuola',
            'regione_scuola', 'nazione_scuola', 'latitudine_scuola', 'longitudine_scuola',
            'indirizzo_completo_scuola', 'scuola_attiva', 'data_creazione_scuola', 'data_modifica_scuola'
        ]
        read_only_fields = ['id', 'data_creazione_scuola', 'data_modifica_scuola']


class UserProfileSerializer(serializers.ModelSerializer):
    nome_completo_utente = serializers.CharField(read_only=True)
    eta_utente = serializers.IntegerField(read_only=True)
    # Compatibility aliases
    user = serializers.PrimaryKeyRelatedField(source='utente', read_only=True)
    nome = serializers.CharField(source='nome_utente', read_only=True)
    cognome = serializers.CharField(source='cognome_utente', read_only=True)

    class Meta:
        model = ProfiloUtente
        fields = [
            'id', 'utente', 'nome_utente', 'cognome_utente', 'sesso_utente', 'data_nascita_utente',
            'codice_fiscale_utente', 'telefono_utente', 'email_personale_utente', 'numero_matricola_utente',
            'classe_utente', 'dipartimento_utente', 'materia_insegnamento_utente', 'preferenze_notifica_utente',
            'preferenze_lingua_utente', 'fuso_orario_utente', 'nome_completo_utente', 'eta_utente',
            'utente_attivo', 'utente_verificato', 'data_verifica_utente', 'ultimo_accesso_utente',
            'data_creazione_utente', 'data_modifica_utente'
        ]
        read_only_fields = ['id', 'utente', 'nome_completo_utente', 'eta_utente', 'data_creazione_utente', 'data_modifica_utente']


class SimpleUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source='profilo_utente', read_only=True)
    # Alias for older frontends
    nome_completo = serializers.SerializerMethodField()

    def get_nome_completo(self, obj):
        profile = getattr(obj, 'profilo_utente', None)
        if profile:
            return getattr(profile, 'nome_completo_utente', None)
        return f"{getattr(obj, 'first_name', '')} {getattr(obj, 'last_name', '')}".strip()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login', 'profile']
        read_only_fields = ['id', 'date_joined', 'last_login', 'profile']


class UserSessionSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(source='utente_sessione', read_only=True)
    is_expired = serializers.BooleanField(read_only=True, source='sessione_scaduta')
    is_valid = serializers.BooleanField(read_only=True, source='sessione_valida')

    class Meta:
        model = SessioneUtente
        fields = [
            'id', 'utente_sessione', 'user', 'tipo_sessione', 'token_sessione', 'pin_sessione',
            'stato_sessione', 'metadati_sessione', 'email_destinazione_sessione',
            'data_creazione_sessione', 'data_scadenza_sessione', 'data_verifica_sessione',
            'is_expired', 'is_valid'
        ]
        read_only_fields = ['id', 'user', 'token_sessione', 'data_creazione_sessione', 'data_scadenza_sessione', 'data_verifica_sessione', 'is_expired', 'is_valid']


class DeviceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaDispositivo
        fields = ['id', 'nome', 'descrizione', 'icona', 'colore', 'attiva', 'ordine']


class ResourceLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UbicazioneRisorsa
        fields = ['id', 'nome', 'descrizione', 'edificio', 'piano', 'aula', 'capacita_persone', 'attrezzature_presenti', 'coordinate_x', 'coordinate_y', 'attivo']


class DeviceSerializer(serializers.ModelSerializer):
    categoria = DeviceCategorySerializer(read_only=True)
    display_name = serializers.CharField(read_only=True, source='display_name')
    is_available = serializers.BooleanField(read_only=True, source='is_available')
    needs_maintenance = serializers.BooleanField(read_only=True, source='needs_maintenance')

    class Meta:
        model = Dispositivo
        fields = ['id', 'nome', 'modello', 'marca', 'serie', 'codice_inventario', 'tipo', 'categoria', 'specifiche', 'stato', 'edificio', 'piano', 'aula', 'armadio', 'data_acquisto', 'data_scadenza_garanzia', 'valore_acquisto', 'note', 'ultimo_controllo', 'prossima_manutenzione', 'display_name', 'is_available', 'needs_maintenance', 'attivo', 'creato_il', 'modificato_il']
        read_only_fields = ['id', 'display_name', 'is_available', 'needs_maintenance', 'creato_il', 'modificato_il']


class ResourceSerializer(serializers.ModelSerializer):
    localizzazione = ResourceLocationSerializer(read_only=True)
    dispositivi = DeviceSerializer(many=True, read_only=True)
    is_laboratorio = serializers.BooleanField(read_only=True, source='is_laboratorio')
    is_carrello = serializers.BooleanField(read_only=True, source='is_carrello')
    is_aula = serializers.BooleanField(read_only=True, source='is_aula')
    is_available_for_booking = serializers.BooleanField(read_only=True, source='is_available_for_booking')
    utilization_stats = serializers.SerializerMethodField()

    class Meta:
        model = Risorsa
        fields = ['id', 'nome', 'codice', 'descrizione', 'tipo', 'categoria', 'localizzazione', 'capacita_massima', 'postazioni_disponibili', 'dispositivi', 'orari_apertura', 'feriali_disponibile', 'weekend_disponibile', 'festivo_disponibile', 'attivo', 'manutenzione', 'bloccato', 'prenotazione_anticipo_minimo', 'prenotazione_anticipo_massimo', 'durata_minima_minuti', 'durata_massima_minuti', 'allow_overbooking', 'overbooking_limite', 'note_amministrative', 'note_utenti', 'is_laboratorio', 'is_carrello', 'is_aula', 'is_available_for_booking', 'utilization_stats', 'creato_il', 'modificato_il']
        read_only_fields = ['id', 'is_laboratorio', 'is_carrello', 'is_aula', 'is_available_for_booking', 'utilization_stats', 'creato_il', 'modificato_il']

    def get_utilization_stats(self, obj):
        from .services import ResourceService
        try:
            return ResourceService.get_resource_utilization(obj, days=30)
        except Exception:
            logging.getLogger('prenotazioni').exception('Failed computing utilization stats for resource %s', getattr(obj, 'id', None))
            return {'total_bookings': 0, 'total_hours': 0, 'average_duration': 0, 'utilization_rate': 0}


class BookingStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatoPrenotazione
        fields = ['id', 'nome', 'descrizione', 'colore', 'icon', 'ordine']


class BookingSerializer(serializers.ModelSerializer):
    utente = SimpleUserSerializer(read_only=True)
    risorsa = ResourceSerializer(read_only=True)
    stato = BookingStatusSerializer(read_only=True)
    dispositivi_selezionati = DeviceSerializer(many=True, read_only=True)

    durata_minuti = serializers.IntegerField(read_only=True, source='durata_minuti')
    durata_ore = serializers.FloatField(read_only=True, source='durata_ore')
    is_passata = serializers.BooleanField(read_only=True, source='is_passata')
    is_futura = serializers.BooleanField(read_only=True, source='is_futura')
    is_in_corso = serializers.BooleanField(read_only=True, source='is_in_corso')

    can_be_modified = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()

    class Meta:
        model = Prenotazione
        fields = ['id', 'utente', 'risorsa', 'dispositivi_selezionati', 'inizio', 'fine', 'quantita', 'priorita', 'stato', 'scopo', 'note', 'note_amministrative', 'setup_needed', 'cleanup_needed', 'approvazione_richiesta', 'approvato_da', 'data_approvazione', 'notifiche_inviate', 'ultimo_aggiornamento_notifica', 'durata_minuti', 'durata_ore', 'is_passata', 'is_futura', 'is_in_corso', 'can_be_modified', 'can_be_cancelled', 'creato_il', 'modificato_il', 'cancellato_il']
        read_only_fields = ['id', 'utente', 'stato', 'approvato_da', 'data_approvazione', 'notifiche_inviate', 'durata_minuti', 'durata_ore', 'is_passata', 'is_futura', 'is_in_corso', 'can_be_modified', 'can_be_cancelled', 'creato_il', 'modificato_il', 'cancellato_il']

    def get_can_be_modified(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return obj.can_be_modified_by(user) if user else False

    def get_can_be_cancelled(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return obj.can_be_cancelled_by(user) if user else False


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prenotazione
        fields = ['risorsa', 'dispositivi_selezionati', 'inizio', 'fine', 'quantita', 'priorita', 'scopo', 'note', 'setup_needed', 'cleanup_needed']

    def validate(self, data):
        inizio = data.get('inizio')
        fine = data.get('fine')
        quantita = data.get('quantita', 1)
        risorsa = data.get('risorsa')

        if inizio and fine and inizio >= fine:
            raise serializers.ValidationError("La data/ora di fine deve essere successiva all'inizio.")
        if quantita <= 0:
            raise serializers.ValidationError("La quantità deve essere positiva.")
        if risorsa and quantita > (risorsa.capacita_massima or 1):
            raise serializers.ValidationError("La quantità richiesta supera la capacità massima.")
        return data

    def create(self, validated_data):
        utente = self.context['request'].user
        initial_status = StatoPrenotazione.objects.get_or_create(nome='pending', defaults={'descrizione': 'In Attesa', 'colore': '#ffc107'})[0]
        booking = Prenotazione.objects.create(utente=utente, stato=initial_status, **validated_data)
        return booking


class SystemLogSerializer(serializers.ModelSerializer):
    utente = SimpleUserSerializer(read_only=True)

    class Meta:
        model = LogSistema
        fields = ['id', 'livello', 'tipo_evento', 'utente', 'messaggio', 'dettagli', 'ip_address', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateNotifica
        fields = ['id', 'nome', 'tipo', 'evento', 'oggetto', 'contenuto', 'attivo', 'creato_il', 'modificato_il']
        read_only_fields = ['id', 'creato_il', 'modificato_il']


class NotificationSerializer(serializers.ModelSerializer):
    utente = SimpleUserSerializer(read_only=True)
    template = NotificationTemplateSerializer(read_only=True)
    related_booking = BookingSerializer(read_only=True)
    related_user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = NotificaUtente
        fields = ['id', 'utente', 'template', 'tipo', 'canale', 'titolo', 'messaggio', 'dati_aggiuntivi', 'stato', 'tentativo_corrente', 'ultimo_tentativo', 'prossimo_tentativo', 'inviata_il', 'consegnata_il', 'errore_messaggio', 'related_booking', 'related_user', 'creato_il']
        read_only_fields = ['id', 'utente', 'template', 'related_booking', 'related_user', 'creato_il']

