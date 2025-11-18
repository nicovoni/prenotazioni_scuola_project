"""
Configurazione Django Admin per la nuova architettura.

Aggiornato per supportare tutti i nuovi modelli della ristrutturazione.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import (
    # Core Models
    Utente, UserProfile, Resource, Device, Booking,
    
    # Configuration & Info
    Configuration, SchoolInfo,
    
    # Session Management
    UserSession,
    
    # Device Management
    DeviceCategory, ResourceLocation,
    
    # Booking Management
    BookingStatus,
    
    # System & Notifications
    SystemLog, NotificationTemplate, Notification,
    
    # File Management
    FileUpload
)


# =====================================================
# ADMIN UTENTI
# =====================================================

@admin.register(Utente)
class UtenteAdmin(UserAdmin):
    """Admin per utenti di sistema con ruoli estesi."""
    
    model = Utente
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'ruolo', 'email_verificato', 'telefono_verificato')
        }),
        (_('Account Status'), {
            'fields': ('account_attivo', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Security'), {
            'fields': ('pin_tentativi', 'pin_bloccato_fino', 'ultimo_login_ip')
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'data_creazione')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'ruolo', 'first_name', 'last_name'),
        }),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'ruolo', 'email_verificato', 'account_attivo', 'is_staff')
    list_filter = ('ruolo', 'email_verificato', 'account_attivo', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    readonly_fields = ('last_login', 'date_joined', 'data_creazione')
    
    def get_readonly_fields(self, request, obj=None):
        """Campi readonly per non-superuser."""
        if not request.user.is_superuser:
            return self.readonly_fields + ('is_staff', 'is_superuser', 'pin_tentativi', 'pin_bloccato_fino')
        return self.readonly_fields


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin per profili utente estesi."""
    
    list_display = ('user', 'nome_completo', 'classe', 'dipartimento', 'attivo', 'verificato')
    list_filter = ('attivo', 'verificato', 'sesso', 'preferenze_lingua')
    search_fields = ('nome', 'cognome', 'user__username', 'user__email', 'classe', 'dipartimento')
    readonly_fields = ('creato_il', 'modificato_il', 'nome_completo', 'eta')
    
    fieldsets = (
        ('User Link', {'fields': ('user',)}),
        ('Informazioni Personali', {
            'fields': ('nome', 'cognome', 'sesso', 'data_nascita', 'codice_fiscale')
        }),
        ('Contatti', {
            'fields': ('telefono', 'email_personale')
        }),
        ('Informazioni Istituzionali', {
            'fields': ('numero_matricola', 'classe', 'dipartimento', 'materia_insegnamento')
        }),
        ('Preferenze', {
            'fields': ('preferenze_notifica', 'preferenze_lingua', 'fuso_orario')
        }),
        ('Status', {
            'fields': ('attivo', 'verificato', 'data_verifica', 'ultimo_accesso')
        }),
    )


# =====================================================
# ADMIN CONFIGURAZIONE
# =====================================================

@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    """Admin per configurazioni di sistema."""
    
    list_display = ('chiave', 'tipo', 'valore_preview', 'modificabile', 'modificato_il')
    list_filter = ('tipo', 'modificabile')
    search_fields = ('chiave', 'descrizione')
    readonly_fields = ('creato_il', 'modificato_il')
    
    fieldsets = (
        ('Configurazione', {
            'fields': ('chiave', 'valore', 'tipo', 'descrizione')
        }),
        ('Controllo', {
            'fields': ('modificabile', 'creato_il', 'modificato_il')
        }),
    )
    
    def valore_preview(self, obj):
        """Mostra anteprima del valore."""
        return obj.valore[:50] + '...' if len(obj.valore) > 50 else obj.valore
    valore_preview.short_description = 'Valore'


@admin.register(SchoolInfo)
class SchoolInfoAdmin(admin.ModelAdmin):
    """Admin per informazioni scuola."""
    
    fieldsets = (
        ('Identificazione', {
            'fields': ('nome_completo', 'nome_breve', 'codice_meccanografico', 'partita_iva')
        }),
        ('Contatti', {
            'fields': ('sito_web', 'email_istituzionale', 'telefono', 'fax')
        }),
        ('Indirizzo', {
            'fields': ('indirizzo', 'cap', 'comune', 'provincia', 'regione', 'nazione')
        }),
        ('Geolocalizzazione', {
            'fields': ('latitudine', 'longitudine')
        }),
        ('Status', {
            'fields': ('attivo', 'creato_il', 'modificato_il')
        }),
    )
    
    readonly_fields = ('creato_il', 'modificato_il')


# =====================================================
# ADMIN SESSIONI
# =====================================================

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin per sessioni utente."""
    
    list_display = ('user', 'tipo', 'stato', 'email_destinazione', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('tipo', 'stato', 'created_at')
    search_fields = ('user__username', 'email_destinazione')
    readonly_fields = ('token', 'created_at', 'expires_at', 'verified_at', 'is_expired', 'is_valid')
    filter_horizontal = ('metadata',) if admin.site.enable_thumbnails else ()
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Scaduta'


# =====================================================
# ADMIN DISPOSITIVI
# =====================================================

@admin.register(DeviceCategory)
class DeviceCategoryAdmin(admin.ModelAdmin):
    """Admin per categorie dispositivi."""
    
    list_display = ('nome', 'ordine', 'attiva', 'icona')
    list_filter = ('attiva',)
    search_fields = ('nome', 'descrizione')
    ordering = ('ordine', 'nome')


@admin.register(ResourceLocation)
class ResourceLocationAdmin(admin.ModelAdmin):
    """Admin per localizzazioni risorse."""
    
    list_display = ('nome', 'edificio', 'piano', 'aula', 'capacita_persone', 'attivo')
    list_filter = ('attivo', 'edificio')
    search_fields = ('nome', 'descrizione', 'edificio', 'aula')


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin per dispositivi."""
    
    list_display = ('display_name', 'tipo', 'categoria', 'stato', 'edificio', 'attivo')
    list_filter = ('tipo', 'stato', 'categoria', 'attivo', 'data_acquisto')
    search_fields = ('nome', 'marca', 'modello', 'serie', 'codice_inventario')
    readonly_fields = ('creato_il', 'modificato_il', 'display_name', 'is_available', 'needs_maintenance')
    
    fieldsets = (
        ('Identificazione', {
            'fields': ('nome', 'modello', 'marca', 'serie', 'codice_inventario')
        }),
        ('Classificazione', {
            'fields': ('tipo', 'categoria')
        }),
        ('Specifiche Tecniche', {
            'fields': ('specifiche',)
        }),
        ('Stato', {
            'fields': ('stato', 'attivo')
        }),
        ('Localizzazione', {
            'fields': ('edificio', 'piano', 'aula', 'armadio')
        }),
        ('Acquisto', {
            'fields': ('data_acquisto', 'data_scadenza_garanzia', 'valore_acquisto')
        }),
        ('Manutenzione', {
            'fields': ('note', 'ultimo_controllo', 'prossima_manutenzione')
        }),
    )


# =====================================================
# ADMIN RISORSE
# =====================================================

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Admin per risorse prenotabili."""
    
    list_display = ('nome', 'codice', 'tipo', 'localizzazione', 'capacita_massima', 'attivo')
    list_filter = ('tipo', 'categoria', 'attivo', 'manutenzione', 'feriali_disponibile', 'weekend_disponibile')
    search_fields = ('nome', 'codice', 'descrizione')
    readonly_fields = ('creato_il', 'modificato_il', 'is_laboratorio', 'is_carrello', 'is_aula', 'is_available_for_booking')
    
    filter_horizontal = ('dispositivi',)
    
    fieldsets = (
        ('Identificazione', {
            'fields': ('nome', 'codice', 'descrizione')
        }),
        ('Classificazione', {
            'fields': ('tipo', 'categoria')
        }),
        ('Localizzazione', {
            'fields': ('localizzazione',)
        }),
        ('Capacità', {
            'fields': ('capacita_massima', 'postazioni_disponibili')
        }),
        ('Dispositivi', {
            'fields': ('dispositivi',)
        }),
        ('Orari', {
            'fields': ('orari_apertura', 'feriali_disponibile', 'weekend_disponibile', 'festivo_disponibile')
        }),
        ('Stato', {
            'fields': ('attivo', 'manutenzione', 'bloccato')
        }),
        ('Preferenze Prenotazione', {
            'fields': ('prenotazione_anticipo_minimo', 'prenotazione_anticipo_massimo', 'durata_minima_minuti', 'durata_massima_minuti')
        }),
        ('Gestione Conflitti', {
            'fields': ('allow_overbooking', 'overbooking_limite')
        }),
        ('Note', {
            'fields': ('note_amministrative', 'note_utenti')
        }),
    )


# =====================================================
# ADMIN PRENOTAZIONI
# =====================================================

@admin.register(BookingStatus)
class BookingStatusAdmin(admin.ModelAdmin):
    """Admin per stati prenotazione."""
    
    list_display = ('nome', 'ordine', 'colore', 'icon')
    list_filter = ('ordine',)
    search_fields = ('nome', 'descrizione')
    ordering = ('ordine', 'nome')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin per prenotazioni."""
    
    list_display = ('utente', 'risorsa', 'stato', 'quantita', 'inizio', 'fine', 'priorita')
    list_filter = ('stato', 'priorita', 'setup_needed', 'cleanup_needed', 'inizio', 'fine')
    search_fields = ('utente__username', 'utente__email', 'risorsa__nome', 'scopo')
    readonly_fields = ('creato_il', 'modificato_il', 'durata_minuti', 'durata_ore', 'is_passata', 'is_futura', 'is_in_corso')
    
    filter_horizontal = ('dispositivi_selezionati',)
    
    fieldsets = (
        ('Relazioni', {
            'fields': ('utente', 'risorsa')
        }),
        ('Dettagli Prenotazione', {
            'fields': ('inizio', 'fine', 'quantita', 'priorita')
        }),
        ('Dispositivi Specifici', {
            'fields': ('dispositivi_selezionati',)
        }),
        ('Informazioni', {
            'fields': ('scopo', 'note')
        }),
        ('Configurazione Speciale', {
            'fields': ('setup_needed', 'cleanup_needed')
        }),
        ('Stato e Workflow', {
            'fields': ('stato', 'approvazione_richiesta', 'approvato_da', 'data_approvazione')
        }),
        ('Note Amministrative', {
            'fields': ('note_amministrative',)
        }),
        ('Cancellazione', {
            'fields': ('cancellato_il',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Campi readonly per prenotazioni passate."""
        readonly = self.readonly_fields
        if obj and obj.is_passata():
            readonly += ('inizio', 'fine', 'stato')
        return readonly


# =====================================================
# ADMIN SISTEMA
# =====================================================

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    """Admin per log di sistema."""
    
    list_display = ('livello', 'tipo_evento', 'utente', 'messaggio_preview', 'timestamp')
    list_filter = ('livello', 'tipo_evento', 'timestamp')
    search_fields = ('utente__username', 'messaggio', 'dettagli')
    readonly_fields = ('timestamp', 'messaggio_preview')
    
    def messaggio_preview(self, obj):
        """Mostra anteprima messaggio."""
        return obj.messaggio[:50] + '...' if len(obj.messaggio) > 50 else obj.messaggio
    messaggio_preview.short_description = 'Messaggio'
    
    def has_add_permission(self, request):
        """Non permette aggiunta manuale di log."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Non permette modifica di log."""
        return False


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin per template notifiche."""
    
    list_display = ('nome', 'tipo', 'evento', 'attivo', 'invio_immediato')
    list_filter = ('tipo', 'attivo', 'invio_immediato')
    search_fields = ('nome', 'evento', 'oggetto', 'contenuto')
    readonly_fields = ('creato_il', 'modificato_il')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin per notifiche."""
    
    list_display = ('utente', 'tipo', 'canale', 'stato', 'titolo', 'creato_il')
    list_filter = ('tipo', 'canale', 'stato', 'creato_il')
    search_fields = ('utente__username', 'titolo', 'messaggio')
    readonly_fields = ('creato_il', 'is_pending', 'can_retry')
    
    def has_add_permission(self, request):
        """Non permette aggiunta manuale di notifiche."""
        return False


# =====================================================
# ADMIN FILE
# =====================================================

@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    """Admin per file caricati."""
    
    list_display = ('nome_originale', 'tipo_file', 'dimensione_formattata', 'caricato_da', 'pubblico', 'creato_il')
    list_filter = ('tipo_file', 'pubblico', 'attivo', 'virus_scanned', 'creato_il')
    search_fields = ('nome_originale', 'titolo', 'descrizione')
    readonly_fields = ('creato_il', 'modificato_il', 'estensione', 'dimensione_formattata', 'download_count', 'ultimo_download')
    
    def dimensione_formattata(self, obj):
        return obj.dimensione_formattata
    dimensione_formattata.short_description = 'Dimensione'


# =====================================================
# BRANDING ADMIN
# =====================================================

# Personalizzazione header admin
admin.site.site_header = f"Sistema Prenotazioni Scolastiche - Amministrazione"
admin.site.site_title = "Admin Sistema Prenotazioni"
admin.site.index_title = "Pannello di Controllo"

# Configurazione media admin
admin.site.enable_thumbnails = True

# Personalizzazione look admin
admin.site.site_url = '/'

# Filtri personalizzati
admin.site.register_action = True
