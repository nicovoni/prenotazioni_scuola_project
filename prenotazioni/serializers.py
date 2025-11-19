"""
Serializers Django REST Framework per la nuova architettura.

Supportano la nuova struttura database con tutti i campi aggiornati.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    Risorsa, Dispositivo, Prenotazione, ConfigurazioneSistema, SessioneUtente,
    LogSistema, TemplateNotifica, NotificaUtente, ProfiloUtente,
    UbicazioneRisorsa, CategoriaDispositivo, StatoPrenotazione, CaricamentoFile, InformazioniScuola
)

# Additional imports needed
from django.contrib.auth.models import User, Group

User = get_user_model()


# =====================================================
# SERIALIZERS CONFIGURAZIONE E SETTINGS
# =====================================================

class ConfigurazioneSistemaSerializer(serializers.ModelSerializer):
    """Serializer per configurazioni di sistema."""

    class Meta:
        model = ConfigurazioneSistema
        fields = [
            'id', 'chiave', 'valore', 'tipo', 'descrizione', 'modificabile',
            'creato_il', 'modificato_il'
        ]
        read_only_fields = ['id', 'creato_il', 'modificato_il']


class SchoolInfoSerializer(serializers.ModelSerializer):
    """Serializer per informazioni scuola."""

    indirizzo_completo = serializers.CharField(read_only=True)

    class Meta:
        model = InformazioniScuola
        fields = [
            'id', 'nome_completo', 'nome_breve', 'codice_meccanografico', 'partita_iva',
            'sito_web', 'email_istituzionale', 'telefono', 'fax',
            'indirizzo', 'cap', 'comune', 'provincia', 'regione', 'nazione',
            'latitudine', 'longitudine', 'indirizzo_completo', 'attivo',
            'creato_il', 'modificato_il'
        ]
        read_only_fields = ['id', 'creato_il', 'modificato_il']


# =====================================================
# SERIALIZERS UTENTI E PROFILI
# =====================================================

class ProfiloUtenteSerializer(serializers.ModelSerializer):
    """Serializer per profilo utente esteso."""

    nome_completo = serializers.CharField(read_only=True)
    eta = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProfiloUtente
        fields = [
            'id', 'user', 'nome', 'cognome', 'sesso', 'data_nascita', 'codice_fiscale',
            'telefono', 'email_personale', 'numero_matricola', 'classe',
            'dipartimento', 'materia_insegnamento', 'preferenze_notifica',
            'preferenze_lingua', 'fuso_orario', 'nome_completo', 'eta',
            'attivo', 'verificato', 'data_verifica', 'ultimo_accesso',
            'creato_il', 'modificato_il'
        ]
        read_only_fields = ['id', 'user', 'nome_completo', 'eta', 'creato_il', 'modificato_il']


class UtenteSerializer(serializers.ModelSerializer):
    """Serializer per utenti di sistema."""

    profile = ProfiloUtenteSerializer(read_only=True)
    nome_completo = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'ruolo', 'first_name', 'last_name',
            'nome_completo', 'profile', 'email_verificato', 'telefono_verificato',
            'account_attivo', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'ultimo_login', 'data_creazione'
        ]
        read_only_fields = [
            'id', 'date_joined', 'ultimo_login', 'data_creazione', 'nome_completo', 'profile'
        ]

    def to_representation(self, instance):
        """Personalizza rappresentazione in base al ruolo dell'utente."""
        data = super().to_representation(instance)

        # Rimuovi campi sensibili per utenti non admin
        request = self.context.get('request')
        if request and not request.user.is_admin():
            sensitive_fields = ['is_active', 'is_staff', 'is_superuser']
            for field in sensitive_fields:
                data.pop(field, None)

        return data


# =====================================================
# SERIALIZERS SESSIONI E VERIFICHE
# =====================================================

class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer per sessioni utente."""

    user = UtenteSerializer(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = SessioneUtente
        fields = [
            'id', 'user', 'tipo', 'token', 'pin', 'stato', 'metadata',
            'email_destinazione', 'created_at', 'expires_at', 'verified_at',
            'is_expired', 'is_valid'
        ]
        read_only_fields = [
            'id', 'user', 'token', 'created_at', 'expires_at',
            'is_expired', 'is_valid'
        ]


# =====================================================
# SERIALIZERS DISPOSITIVI E RISORSE
# =====================================================

class DeviceCategorySerializer(serializers.ModelSerializer):
    """Serializer per categorie dispositivi."""

    class Meta:
        model = CategoriaDispositivo
        fields = ['id', 'nome', 'descrizione', 'icona', 'colore', 'attiva', 'ordine']


class ResourceLocationSerializer(serializers.ModelSerializer):
    """Serializer per localizzazioni."""

    class Meta:
        model = UbicazioneRisorsa
        fields = [
            'id', 'nome', 'descrizione', 'edificio', 'piano', 'aula',
            'capacita_persone', 'attrezzature_presenti', 'coordinate_x',
            'coordinate_y', 'attivo'
        ]


class Dispositivoserializer(serializers.ModelSerializer):
    """Serializer per dispositivi."""

    categoria = DeviceCategorySerializer(read_only=True)
    display_name = serializers.CharField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    needs_maintenance = serializers.BooleanField(read_only=True)

    class Meta:
        model = Dispositivo
        fields = [
            'id', 'nome', 'modello', 'marca', 'serie', 'codice_inventario',
            'tipo', 'categoria', 'specifiche', 'stato', 'edificio', 'piano',
            'aula', 'armadio', 'data_acquisto', 'data_scadenza_garanzia',
            'valore_acquisto', 'note', 'ultimo_controllo', 'prossima_manutenzione',
            'display_name', 'is_available', 'needs_maintenance',
            'attivo', 'creato_il', 'modificato_il'
        ]
        read_only_fields = [
            'id', 'display_name', 'is_available', 'needs_maintenance',
            'creato_il', 'modificato_il'
        ]


class RisorsaSerializer(serializers.ModelSerializer):
    """Serializer per risorse prenotabili."""

    localizzazione = ResourceLocationSerializer(read_only=True)
    dispositivi = Dispositivoserializer(many=True, read_only=True)

    # Metodi di utilità
    is_laboratorio = serializers.BooleanField(read_only=True)
    is_carrello = serializers.BooleanField(read_only=True)
    is_aula = serializers.BooleanField(read_only=True)
    is_available_for_booking = serializers.BooleanField(read_only=True)

    # Statistiche utilizzo
    utilization_stats = serializers.SerializerMethodField()

    class Meta:
        model = Risorsa
        fields = [
            'id', 'nome', 'codice', 'descrizione', 'tipo', 'categoria',
            'localizzazione', 'capacita_massima', 'postazioni_disponibili',
            'dispositivi', 'orari_apertura', 'feriali_disponibile',
            'weekend_disponibile', 'festivo_disponibile', 'attivo',
            'manutenzione', 'bloccato', 'prenotazione_anticipo_minimo',
            'prenotazione_anticipo_massimo', 'durata_minima_minuti',
            'durata_massima_minuti', 'allow_overbooking', 'overbooking_limite',
            'note_amministrative', 'note_utenti', 'is_laboratorio',
            'is_carrello', 'is_aula', 'is_available_for_booking',
            'utilization_stats', 'creato_il', 'modificato_il'
        ]
        read_only_fields = [
            'id', 'is_laboratorio', 'is_carrello', 'is_aula',
            'is_available_for_booking', 'utilization_stats',
            'creato_il', 'modificato_il'
        ]

    def get_utilization_stats(self, obj):
        """Calcola statistiche utilizzo risorsa."""
        from .services import ResourceService
        try:
            stats = ResourceService.get_resource_utilization(obj, days=30)
            return stats
        except Exception:
            return {
                'total_bookings': 0,
                'total_hours': 0,
                'average_duration': 0,
                'utilization_rate': 0
            }


# =====================================================
# SERIALIZERS PRENOTAZIONI
# =====================================================

class BookingStatusSerializer(serializers.ModelSerializer):
    """Serializer per stati prenotazione."""

    class Meta:
        model = StatoPrenotazione
        fields = ['id', 'nome', 'descrizione', 'colore', 'icon', 'ordine']


class PrenotazioneSerializer(serializers.ModelSerializer):
    """Serializer per prenotazioni."""

    utente = UtenteSerializer(read_only=True)
    risorsa = RisorsaSerializer(read_only=True)
    stato = BookingStatusSerializer(read_only=True)
    dispositivi_selezionati = Dispositivoserializer(many=True, read_only=True)

    # Proprietà calcolate
    durata_minuti = serializers.IntegerField(read_only=True)
    durata_ore = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    is_passata = serializers.BooleanField(read_only=True)
    is_futura = serializers.BooleanField(read_only=True)
    is_in_corso = serializers.BooleanField(read_only=True)

    # Azioni disponibili
    can_be_modified = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()

    class Meta:
        model = Prenotazione
        fields = [
            'id', 'utente', 'risorsa', 'dispositivi_selezionati', 'inizio', 'fine',
            'quantita', 'priorita', 'stato', 'scopo', 'note', 'note_amministrative',
            'setup_needed', 'cleanup_needed', 'approvazione_richiesta',
            'approvato_da', 'data_approvazione', 'notifiche_inviate',
            'ultimo_aggiornamento_notifica', 'durata_minuti', 'durata_ore',
            'is_passata', 'is_futura', 'is_in_corso', 'can_be_modified',
            'can_be_cancelled', 'creato_il', 'modificato_il', 'cancellato_il'
        ]
        read_only_fields = [
            'id', 'utente', 'stato', 'approvato_da', 'data_approvazione',
            'notifiche_inviate', 'durata_minuti', 'durata_ore',
            'is_passata', 'is_futura', 'is_in_corso', 'can_be_modified',
            'can_be_cancelled', 'creato_il', 'modificato_il', 'cancellato_il'
        ]

    def get_can_be_modified(self, obj):
        """Verifica se la prenotazione può essere modificata."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Simplified check - in a real app you might check status, time, permissions etc.
            return True
        return False

    def get_can_be_cancelled(self, obj):
        """Verifica se la prenotazione può essere cancellata."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Simplified check - in a real app you might check status, time, permissions etc.
            return True
        return False


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer per creazione prenotazioni."""

    class Meta:
        model = Prenotazione
        fields = [
            'risorsa', 'dispositivi_selezionati', 'inizio', 'fine',
            'quantita', 'priorita', 'scopo', 'note', 'setup_needed', 'cleanup_needed'
        ]

    def validate(self, data):
        """Validazioni personalizzate."""
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
        """Crea prenotazione associandola all'utente."""
        utente = self.context['request'].user

        # Determina stato iniziale
        initial_status = StatoPrenotazione.objects.get_or_create(
            nome='pending',
            defaults={'descrizione': 'In Attesa', 'colore': '#ffc107'}
        )[0]

        booking = Prenotazione.objects.create(
            utente=utente,
            stato=initial_status,
            **validated_data
        )

        return booking


# =====================================================
# SERIALIZERS SISTEMA E LOG
# =====================================================

class LogSistemaSerializer(serializers.ModelSerializer):
    """Serializer per log di sistema."""

    utente = UtenteSerializer(read_only=True)

    class Meta:
        model = LogSistema
        fields = [
            'id', 'livello', 'tipo_evento', 'utente', 'messaggio', 'dettagli',
            'ip_address', 'user_agent', 'request_path', 'metodo_http',
            'object_type', 'object_id', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer per template notifiche."""

    class Meta:
        model = TemplateNotifica
        fields = [
            'id', 'nome', 'tipo', 'evento', 'oggetto', 'contenuto',
            'attivo', 'invio_immediato', 'tentativi_massimi',
            'intervallo_tentativi_minuti', 'variabili_disponibili',
            'creato_il', 'modificato_il'
        ]
        read_only_fields = ['id', 'creato_il', 'modificato_il']


class NotificaUtenteSerializer(serializers.ModelSerializer):
    """Serializer per notifiche."""

    utente = UtenteSerializer(read_only=True)
    template = NotificationTemplateSerializer(read_only=True)
    related_booking = PrenotazioneSerializer(read_only=True)
    related_user = UtenteSerializer(read_only=True)

    is_pending = serializers.BooleanField(read_only=True)
    can_retry = serializers.BooleanField(read_only=True)

    class Meta:
        model = NotificaUtente
        fields = [
            'id', 'utente', 'template', 'tipo', 'canale', 'titolo', 'messaggio',
            'dati_aggiuntivi', 'stato', 'tentativo_corrente', 'ultimo_tentativo',
            'prossimo_tentativo', 'inviata_il', 'consegnata_il', 'errore_messaggio',
            'related_booking', 'related_user', 'is_pending', 'can_retry',
            'creato_il'
        ]
        read_only_fields = [
            'id', 'utente', 'template', 'related_booking', 'related_user',
            'is_pending', 'can_retry', 'creato_il'
        ]


# =====================================================
# SERIALIZERS STATISTICHE E REPORT
# =====================================================

class SystemStatsSerializer(serializers.Serializer):
    """Serializer per statistiche sistema."""
    
    users = serializers.DictField()
    resources = serializers.DictField()
    devices = serializers.DictField()
    bookings = serializers.DictField()
    system = serializers.DictField()


class ResourceUtilizationSerializer(serializers.Serializer):
    """Serializer per statistiche utilizzo risorse."""

    resource = RisorsaSerializer(read_only=True)
    total_bookings = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=8, decimal_places=2)
    average_duration = serializers.DecimalField(max_digits=6, decimal_places=2)
    utilization_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    peak_hours = serializers.DictField(allow_null=True)


class DeviceUsageStatsSerializer(serializers.Serializer):
    """Serializer per statistiche utilizzo dispositivi."""

    device = Dispositivoserializer(read_only=True)
    total_bookings = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=8, decimal_places=2)
    average_duration = serializers.DecimalField(max_digits=6, decimal_places=2)
    utilization_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


# =====================================================
# SERIALIZERS FILE E ALLEGATI
# =====================================================

class FileUploadSerializer(serializers.ModelSerializer):
    """Serializer per file caricati."""

    caricato_da = UtenteSerializer(read_only=True)
    estensione = serializers.CharField(read_only=True)
    dimensione_formattata = serializers.CharField(read_only=True)

    class Meta:
        model = CaricamentoFile
        fields = [
            'id', 'file', 'nome_originale', 'dimensione', 'tipo_mime',
            'tipo_file', 'titolo', 'descrizione', 'tags', 'checksum',
            'virus_scanned', 'scan_result', 'caricato_da', 'pubblico',
            'attivo', 'download_count', 'ultimo_download', 'estensione',
            'dimensione_formattata', 'creato_il', 'modificato_il'
        ]
        read_only_fields = [
            'id', 'caricato_da', 'estensione', 'dimensione_formattata',
            'download_count', 'ultimo_download', 'creato_il', 'modificato_il'
        ]


# =====================================================
# SERIALIZERS SPECIALI E AGGREGATI
# =====================================================

class BookingSummarySerializer(serializers.Serializer):
    """Serializer per riassunto prenotazioni."""
    
    total_bookings = serializers.IntegerField()
    active_bookings = serializers.IntegerField()
    cancelled_bookings = serializers.IntegerField()
    upcoming_bookings = serializers.IntegerField()
    today_bookings = serializers.IntegerField()
    this_week_bookings = serializers.IntegerField()
    most_booked_resource = serializers.CharField()
    peak_booking_hour = serializers.IntegerField()
    average_booking_duration = serializers.DecimalField(max_digits=6, decimal_places=2)


class UserActivitySerializer(serializers.Serializer):
    """Serializer per attività utente."""
    
    user = UtenteSerializer(read_only=True)
    total_bookings = serializers.IntegerField()
    bookings_this_month = serializers.IntegerField()
    favorite_resource = serializers.CharField(allow_null=True)
    average_booking_duration = serializers.DecimalField(max_digits=6, decimal_places=2)
    last_booking = serializers.DateTimeField(allow_null=True)
    booking_trend = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=True
    )


class SystemHealthSerializer(serializers.Serializer):
    """Serializer per salute sistema."""
    
    status = serializers.CharField()
    database_connection = serializers.CharField()
    active_sessions = serializers.IntegerField()
    pending_notifications = serializers.IntegerField()
    disk_usage = serializers.CharField(allow_null=True)
    memory_usage = serializers.CharField(allow_null=True)
    cpu_usage = serializers.CharField(allow_null=True)
    last_backup = serializers.DateTimeField(allow_null=True)
    uptime = serializers.CharField(allow_null=True)
    timestamp = serializers.DateTimeField()


# =====================================================
# NESTED SERIALIZERS PER API AVANZATE
# =====================================================

class BookingWithDetailsSerializer(BookingSerializer):
    """Serializer esteso per prenotazioni con dettagli."""
    
    resource_details = ResourceSerializer(source='risorsa', read_only=True)
    user_details = UtenteSerializer(source='utente', read_only=True)
    related_notifications = serializers.SerializerMethodField()
    
    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + [
            'resource_details', 'user_details', 'related_notifications'
        ]
    
    def get_related_notifications(self, obj):
        """Notifiche correlate alla prenotazione."""
        notifications = obj.notification_set.all()[:5]
        return NotificationSerializer(notifications, many=True, context=self.context).data


class UserWithStatsSerializer(UtenteSerializer):
    """Serializer esteso per utenti con statistiche."""
    
    booking_stats = serializers.SerializerMethodField()
    activity_summary = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta(UtenteSerializer.Meta):
        fields = UtenteSerializer.Meta.fields + [
            'booking_stats', 'activity_summary', 'permissions'
        ]
    
    def get_booking_stats(self, obj):
        """Statistiche prenotazioni utente."""
        from .services import BookingService
        return BookingService.get_user_bookings(obj).count()
    
    def get_activity_summary(self, obj):
        """Riassunto attività utente."""
        return {
            'last_login': obj.last_login,
            'total_sessions': obj.sessions.count(),
            'profile_completion': self._calculate_profile_completion(obj)
        }
    
    def get_permissions(self, obj):
        """Permessi utente basati sul ruolo."""
        return {
            'can_book': obj.is_active,
            'can_modify_own_bookings': True,
            'can_modify_all_bookings': obj.is_superuser,
            'can_access_admin': obj.is_staff,
            'can_manage_resources': obj.is_staff,
            'can_manage_users': obj.is_superuser
        }
    
    def _calculate_profile_completion(self, user):
        """Calcola percentuale completamento profilo."""
        if hasattr(user, 'profile'):
            profile = user.profile
            fields = ['nome', 'cognome', 'telefono', 'data_nascita']
            completed = sum(1 for field in fields if getattr(profile, field))
            return int((completed / len(fields)) * 100)
        return 0
