"""
Configurazione Django Admin per la nuova architettura.

Aggiornato per supportare tutti i nuovi modelli della ristrutturazione.
"""

from django.contrib import admin
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

    list_display = ('nome', 'tipo', 'categoria', 'stato', 'disponibile', 'edificio', 'attivo')
    list_filter = ('tipo', 'stato', 'categoria', 'attivo', 'data_acquisto')
    search_fields = ('nome', 'marca', 'modello', 'serie', 'codice_inventario')
    readonly_fields = ('creato_il', 'modificato_il', 'disponibile')

    def disponibile(self, obj):
        """Mostra se il dispositivo è disponibile."""
        return obj.is_available()
    disponibile.boolean = True
    disponibile.short_description = 'Disponibile'


# =====================================================
# ADMIN RISORSE
# =====================================================

@admin.register(Risorsa)
class AmministrazioneRisorsa(admin.ModelAdmin):
    """Admin per risorse prenotabili."""

    list_display = ('nome', 'codice', 'tipo', 'localizzazione', 'capacita_massima', 'attivo')
    list_filter = ('tipo', 'categoria', 'attivo', 'manutenzione', 'feriali_disponibile', 'weekend_disponibile')
    search_fields = ('nome', 'codice', 'descrizione')
    readonly_fields = ('creato_il', 'modificato_il')

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
    """Admin per prenotazioni - Controllo MINUZIOSO e completo."""

    list_display = ('utente', 'risorsa', 'stato', 'quantita', 'inizio', 'fine', 'priorita', 'durata_ore', 'stato_temporale', 'con_approvazione', 'modificabile', 'dispositivi_richiesti')
    list_filter = ('stato', 'priorita', 'setup_needed', 'cleanup_needed', 'inizio', 'fine', 'approvazione_richiesta')
    search_fields = ('utente__username', 'utente__email', 'risorsa__nome', 'scopo', 'dispositivi_selezionati__nome')
    readonly_fields = ('creato_il', 'modificato_il', 'durata_minuti', 'durata_ore', 'stato_temporale', 'con_approvazione', 'modificabile', 'cancellabile', 'conflitti', 'dispositivi_richiesti', 'data_approvazione')

    filter_horizontal = ('dispositivi_selezionati',)

    # Filtri avanzati per controllo minuzioso
    list_filter = (
        'stato',
        'priorita',
        'setup_needed',
        'cleanup_needed',
        'approvazione_richiesta',
        ('risorsa', admin.RelatedOnlyFieldListFilter),
        ('inizio', admin.DateFieldListFilter),
        ('fine', admin.DateFieldListFilter),
    )

    def durata_minuti(self, obj):
        """Mostra durata in minuti."""
        return obj.durata_minuti if hasattr(obj, 'durata_minuti') else 0
    durata_minuti.short_description = 'Durata (minuti)'

    def durata_ore(self, obj):
        """Mostra durata in ore."""
        return obj.durata_ore if hasattr(obj, 'durata_ore') else 0
    durata_ore.short_description = 'Durata (ore)'

    def stato_temporale(self, obj):
        """Mostra stato temporale della prenotazione."""
        if hasattr(obj, 'is_passata') and hasattr(obj, 'is_in_corso'):
            if obj.is_passata():
                return "Passata"
            elif obj.is_in_corso():
                return "In Corso"
            else:
                return "Futura"
        return "Sconosciuto"
    stato_temporale.short_description = 'Stato Temporale'

    def con_approvazione(self, obj):
        """Mostra se la prenotazione richiede/è stata approvata."""
        if obj.approvazione_richiesta:
            if obj.data_approvazione:
                return f"Approvata ({obj.approvato_da})" if obj.approvato_da else "Approvata"
            else:
                return "Da Approvare"
        return "Auto-Approvata"
    con_approvazione.short_description = 'Approvazione'
    con_approvazione.admin_order_field = 'approvazione_richiesta'

    def modificabile(self, obj):
        """Verifica se la prenotazione può essere modificata."""
        # Logica di controllo minuziosa
        if hasattr(obj, 'is_passata') and obj.is_passata():
            return "No - Passata"
        if obj.stato and obj.stato.nome == 'cancelled':
            return "No - Cancellata"
        return "Sì"
    modificabile.short_description = 'Modificabile'

    def cancellabile(self, obj):
        """Verifica se la prenotazione può essere cancellata."""
        if hasattr(obj, 'is_passata') and obj.is_passata():
            return "No - Passata"
        if obj.stato and obj.stato.nome == 'cancelled':
            return "Già Cancellata"
        return "Sì"
    cancellabile.short_description = 'Cancellabile'

    def conflitti(self, obj):
        """Rileva possibili conflitti di prenotazione."""
        # Controllo semplificato di sovrapposizioni
        conflitti_count = Prenotazione.objects.filter(
            risorsa=obj.risorsa,
            inizio__lt=obj.fine,
            fine__gt=obj.inizio
        ).exclude(pk=obj.pk).count()

        if conflitti_count > 0:
            return f"⚠️ {conflitti_count} conflitti"
        return "✅ Nessun conflitto"
    conflitti.short_description = 'Conflitti'

    def dispositivi_richiesti(self, obj):
        """Mostra i dispositivi richiesti per questa prenotazione."""
        dispositivi = obj.dispositivi_selezionati.all()
        if dispositivi:
            return ", ".join([d.nome for d in dispositivi[:3]]) + (f" +{dispositivi.count()-3}" if dispositivi.count() > 3 else "")
        return "Nessuno"
    dispositivi_richiesti.short_description = 'Dispositivi'

    def get_queryset(self, request):
        """Ottimizza le query per controlli minuziosi."""
        return super().get_queryset(request).select_related(
            'utente', 'risorsa', 'stato', 'approvato_da'
        ).prefetch_related('dispositivi_selezionati')

    def get_readonly_fields(self, request, obj=None):
        """Campi readonly basati su logica minuziosa."""
        readonly = list(self.readonly_fields)

        if obj:
            # Prenotazioni passate diventano in sola lettura completamente
            if hasattr(obj, 'is_passata') and obj.is_passata():
                readonly.extend(['inizio', 'fine', 'stato', 'quantita'])

            # Prenotazioni cancellate bloccano le modifiche
            if obj.stato and obj.stato.nome == 'cancelled':
                readonly.extend(['inizio', 'fine', 'quantita'])

        return tuple(readonly)


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

    list_display = ('nome', 'tipo', 'evento', 'attivo')
    list_filter = ('tipo', 'attivo')
    search_fields = ('nome', 'evento', 'oggetto', 'contenuto')
    readonly_fields = ('creato_il', 'modificato_il')


@admin.register(NotificaUtente)
class AmministrazioneNotifica(admin.ModelAdmin):
    """Admin per notifiche."""

    list_display = ('utente', 'tipo', 'canale', 'stato', 'titolo', 'creato_il')
    list_filter = ('tipo', 'canale', 'stato', 'creato_il')
    search_fields = ('utente__username', 'titolo', 'messaggio')
    readonly_fields = ('creato_il',)

    def has_add_permission(self, request):
        """Non permette aggiunta manuale di notifiche."""
        return False


# =====================================================
# ADMIN FILE
# =====================================================

@admin.register(CaricamentoFile)
class AmministrazioneCaricamentoFile(admin.ModelAdmin):
    """Admin per file caricati."""

    list_display = ('nome_originale', 'tipo_file', 'dimensione', 'caricato_da', 'pubblico', 'creato_il')
    list_filter = ('tipo_file', 'pubblico', 'attivo', 'virus_scanned', 'creato_il')
    search_fields = ('nome_originale', 'titolo', 'descrizione')
    readonly_fields = ('creato_il', 'modificato_il')


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
