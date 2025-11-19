"""
Configurazione Django Admin per la nuova architettura.

Aggiornato per supportare tutti i nuovi modelli della ristrutturazione.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import (
    # Modelli Core
    ProfiloUtente, Risorsa, Dispositivo, Prenotazione,

    # Configurazione e Info
    ConfigurazioneSistema, InformazioniScuola,

    # Gestione Sessioni
    SessioneUtente,

    # Gestione Dispositivi
    CategoriaDispositivo, UbicazioneRisorsa,

    # Gestione Prenotazioni
    StatoPrenotazione,

    # Sistema e Notifiche
    LogSistema, TemplateNotifica, NotificaUtente,

    # Gestione File
    CaricamentoFile
)


# =====================================================
# ADMIN UTENTI
# =====================================================

# Using Django's built-in User admin - custom user profile fields are managed via ProfiloUtente admin


@admin.register(ProfiloUtente)
class AmministrazioneProfiloUtente(admin.ModelAdmin):
    """Admin per profili utente estesi."""

    list_display = ('utente', 'nome_completo_utente', 'classe_utente', 'dipartimento_utente', 'utente_attivo', 'utente_verificato')
    list_filter = ('utente_attivo', 'utente_verificato', 'sesso_utente', 'preferenze_lingua_utente')
    search_fields = ('nome_utente', 'cognome_utente', 'utente__username', 'utente__email', 'classe_utente', 'dipartimento_utente')
    readonly_fields = ('data_creazione_utente', 'data_modifica_utente', 'nome_completo_utente', 'eta_utente')


# =====================================================
# ADMIN CONFIGURAZIONE
# =====================================================

@admin.register(ConfigurazioneSistema)
class AmministrazioneConfigurazioneSistema(admin.ModelAdmin):
    """Admin per configurazioni di sistema."""

    list_display = ('chiave_configurazione', 'tipo_configurazione', 'anteprima_valore', 'configurazione_modificabile', 'data_modifica_configurazione')
    list_filter = ('tipo_configurazione', 'configurazione_modificabile')
    search_fields = ('chiave_configurazione', 'descrizione_configurazione')
    readonly_fields = ('data_creazione_configurazione', 'data_modifica_configurazione')

    def anteprima_valore(self, obj):
        """Mostra anteprima del valore."""
        return obj.valore_configurazione[:50] + '...' if len(obj.valore_configurazione) > 50 else obj.valore_configurazione
    anteprima_valore.short_description = 'Valore'


@admin.register(InformazioniScuola)
class AmministrazioneInformazioniScuola(admin.ModelAdmin):
    """Admin per informazioni scuola."""

    fieldsets = (
        ('Identificazione', {
            'fields': ('nome_completo_scuola', 'nome_breve_scuola', 'codice_meccanografico_scuola', 'partita_iva_scuola')
        }),
        ('Contatti', {
            'fields': ('sito_web_scuola', 'email_istituzionale_scuola', 'telefono_scuola', 'fax_scuola')
        }),
        ('Indirizzo', {
            'fields': ('indirizzo_scuola', 'codice_postale_scuola', 'comune_scuola', 'provincia_scuola', 'regione_scuola', 'nazione_scuola')
        }),
        ('Geolocalizzazione', {
            'fields': ('latitudine_scuola', 'longitudine_scuola')
        }),
        ('Status', {
            'fields': ('scuola_attiva', 'data_creazione_scuola', 'data_modifica_scuola')
        }),
    )

    readonly_fields = ('data_creazione_scuola', 'data_modifica_scuola')


# =====================================================
# ADMIN SESSIONI
# =====================================================

@admin.register(SessioneUtente)
class AmministrazioneSessioneUtente(admin.ModelAdmin):
    """Admin per sessioni utente."""

    list_display = ('utente_sessione', 'tipo_sessione', 'stato_sessione', 'email_destinazione_sessione', 'data_creazione_sessione', 'data_scadenza_sessione', 'sessione_scaduta')
    list_filter = ('tipo_sessione', 'stato_sessione', 'data_creazione_sessione')
    search_fields = ('utente_sessione__username', 'email_destinazione_sessione')
    readonly_fields = ('token_sessione', 'data_creazione_sessione', 'data_scadenza_sessione', 'data_verifica_sessione', 'sessione_scaduta', 'sessione_valida')

    def sessione_scaduta(self, obj):
        return obj.sessione_scaduta
    sessione_scaduta.boolean = True
    sessione_scaduta.short_description = 'Scaduta'


# =====================================================
# ADMIN DISPOSITIVI
# =====================================================

@admin.register(CategoriaDispositivo)
class AmministrazioneCategoriaDispositivo(admin.ModelAdmin):
    """Admin per categorie dispositivi."""

    list_display = ('nome', 'ordine', 'attiva', 'icona')
    list_filter = ('attiva',)
    search_fields = ('nome', 'descrizione')
    ordering = ('ordine', 'nome')


@admin.register(UbicazioneRisorsa)
class AmministrazioneUbicazioneRisorsa(admin.ModelAdmin):
    """Admin per localizzazioni risorse."""

    list_display = ('nome', 'edificio', 'piano', 'aula', 'capacita_persone', 'attivo')
    list_filter = ('attivo', 'edificio')
    search_fields = ('nome', 'descrizione', 'edificio', 'aula')


@admin.register(Dispositivo)
class AmministrazioneDispositivo(admin.ModelAdmin):
    """Admin per dispositivi."""

    list_display = ('display_name', 'tipo', 'categoria', 'stato', 'edificio', 'attivo')
    list_filter = ('tipo', 'stato', 'categoria', 'attivo', 'data_acquisto')
    search_fields = ('nome', 'marca', 'modello', 'serie', 'codice_inventario')
    readonly_fields = ('creato_il', 'modificato_il', 'display_name', 'is_available', 'needs_maintenance')


# =====================================================
# ADMIN RISORSE
# =====================================================

@admin.register(Risorsa)
class AmministrazioneRisorsa(admin.ModelAdmin):
    """Admin per risorse prenotabili."""

    list_display = ('nome', 'codice', 'tipo', 'localizzazione', 'capacita_massima', 'attivo')
    list_filter = ('tipo', 'categoria', 'attivo', 'manutenzione', 'feriali_disponibile', 'weekend_disponibile')
    search_fields = ('nome', 'codice', 'descrizione')
    readonly_fields = ('creato_il', 'modificato_il', 'is_laboratorio', 'is_carrello', 'is_aula', 'is_available_for_booking')

    filter_horizontal = ('dispositivi',)


# =====================================================
# ADMIN PRENOTAZIONI
# =====================================================

@admin.register(StatoPrenotazione)
class AmministrazioneStatoPrenotazione(admin.ModelAdmin):
    """Admin per stati prenotazione."""

    list_display = ('nome', 'ordine', 'colore', 'icon')
    list_filter = ('ordine',)
    search_fields = ('nome', 'descrizione')
    ordering = ('ordine', 'nome')


@admin.register(Prenotazione)
class AmministrazionePrenotazione(admin.ModelAdmin):
    """Admin per prenotazioni."""

    list_display = ('utente', 'risorsa', 'stato', 'quantita', 'inizio', 'fine', 'priorita')
    list_filter = ('stato', 'priorita', 'setup_needed', 'cleanup_needed', 'inizio', 'fine')
    search_fields = ('utente__username', 'utente__email', 'risorsa__nome', 'scopo')
    readonly_fields = ('creato_il', 'modificato_il', 'durata_minuti', 'durata_ore', 'is_passata', 'is_futura', 'is_in_corso')

    filter_horizontal = ('dispositivi_selezionati',)

    def get_readonly_fields(self, request, obj=None):
        """Campi readonly per prenotazioni passate."""
        readonly = self.readonly_fields
        if obj and obj.is_passata():
            readonly += ('inizio', 'fine', 'stato')
        return readonly


# =====================================================
# ADMIN SISTEMA
# =====================================================

@admin.register(LogSistema)
class AmministrazioneLogSistema(admin.ModelAdmin):
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


@admin.register(TemplateNotifica)
class AmministrazioneTemplateNotifica(admin.ModelAdmin):
    """Admin per template notifiche."""

    list_display = ('nome', 'tipo', 'evento', 'attivo', 'invio_immediato')
    list_filter = ('tipo', 'attivo', 'invio_immediato')
    search_fields = ('nome', 'evento', 'oggetto', 'contenuto')
    readonly_fields = ('creato_il', 'modificato_il')


# Fix the import - NotificaUtente is not the model name, let's check what it actually is
@admin.register(NotificaUtente)
class AmministrazioneNotifica(admin.ModelAdmin):
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

@admin.register(CaricamentoFile)
class AmministrazioneCaricamentoFile(admin.ModelAdmin):
    """Admin per file caricati."""

    list_display = ('nome_originale', 'tipo_file', 'dimensione_formattata', 'caricato_da', 'pubblico', 'creato_il')
    list_filter = ('tipo_file', 'pubblico', 'attivo', 'virus_scanned', 'creato_il')
    search_fields = ('nome_originale', 'titolo', 'descrizione')
    readonly_fields = ('creato_il', 'modificato_il', 'estensione', 'dimensione_formattata', 'download_count', 'ultimo_download')

    def dimensione_formattata(self, obj):
        return obj.dimensione_formattata


# =====================================================
# BRANDING ADMIN
# =====================================================

# Personalizzazione header admin
admin.site.site_header = "Sistema Prenotazioni Scolastiche - Amministrazione"
admin.site.site_title = "Admin Sistema Prenotazioni"
admin.site.index_title = "Pannello di Controllo"

# Personalizzazione look admin
admin.site.site_url = '/'

# Configurazione di base completa
admin.site.site_header = "Sistema Prenotazioni Scolastiche - Amministrazione"
