Replace file with consolidated serializers content from backup for improved mappings and fields
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

    device = DispositivoSerializer(read_only=True)
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

class BookingWithDetailsSerializer(PrenotazioneSerializer):
    """Serializer esteso per prenotazioni con dettagli."""

    resource_details = RisorsaSerializer(source='risorsa', read_only=True)
    user_details = UtenteSerializer(source='utente', read_only=True)
    related_notifications = serializers.SerializerMethodField()

    class Meta(PrenotazioneSerializer.Meta):
        fields = PrenotazioneSerializer.Meta.fields + [
            'resource_details', 'user_details', 'related_notifications'
        ]

    def get_related_notifications(self, obj):
        """Notifiche correlate alla prenotazione."""
        notifications = obj.notificautente_set.all()[:5]  # Changed from notification_set to notificautente_set
        return NotificaUtenteSerializer(notifications, many=True, context=self.context).data


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
        if hasattr(user, 'profilo_utente'):
            profile = getattr(user, 'profilo_utente')
            fields = ['nome_utente', 'cognome_utente', 'telefono_utente', 'data_nascita_utente']
            completed = sum(1 for field in fields if getattr(profile, field, None))
            return int((completed / len(fields)) * 100)
        return 0
