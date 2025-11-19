"""
Sistema di prenotazioni scolastiche - NUOVA ARCHITETTURA MIGLIORATA

Ristrutturazione completa del database con miglioramenti architetturali:
- Normalizzazione migliore dei dati
- Gestione stato e transizioni
- Audit trail completo
- Configurazione centralizzata
- Gestione sessioni e verifiche
- Sistema di log e monitoraggio
- Gestione notifiche avanzata
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, User
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid


# =============================================================================
# UTENSILI AUSILIARI
# =============================================================================

def genera_codice_univoco():
    """Genera un codice univoco per elementi del sistema."""
    return str(uuid.uuid4())


# =====================================================
# CONFIGURAZIONE E SETTINGS
# =====================================================

class ConfigurazioneSistema(models.Model):
    """
    Configurazione centralizzata del sistema.

    Sostituisce settings.py dispersi con configurazione database-driven.
    """
    TIPO_CONFIGURAZIONE = [
        ('email', 'Email/SMTP'),
        ('prenotazioni', 'Prenotazioni'),
        ('sistema', 'Sistema'),
        ('interfaccia', 'Interfaccia'),
        ('sicurezza', 'Sicurezza'),
    ]

    chiave_configurazione = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Chiave Configurazione',
        help_text='Identificatore univoco (es: HOST_EMAIL, ORA_INIZIO_PRENOTAZIONI)'
    )
    valore_configurazione = models.TextField(
        verbose_name='Valore',
        help_text='Valore della configurazione'
    )
    tipo_configurazione = models.CharField(
        max_length=20,
        choices=TIPO_CONFIGURAZIONE,
        verbose_name='Tipo Configurazione',
        help_text='Categoria della configurazione'
    )
    descrizione_configurazione = models.TextField(
        blank=True,
        verbose_name='Descrizione',
        help_text='Descrizione della configurazione'
    )
    configurazione_modificabile = models.BooleanField(
        default=True,
        verbose_name='Modificabile',
        help_text='Se la configurazione può essere modificata da amministratore'
    )
    data_creazione_configurazione = models.DateTimeField(auto_now_add=True)
    data_modifica_configurazione = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configurazione Sistema'
        verbose_name_plural = 'Configurazioni Sistema'
        ordering = ['tipo_configurazione', 'chiave_configurazione']
        indexes = [
            models.Index(fields=['chiave_configurazione']),
            models.Index(fields=['tipo_configurazione']),
        ]

    def __str__(self):
        return f"{self.chiave_configurazione}: {self.valore_configurazione[:50]}..."

    @classmethod
    def ottieni_configurazione(cls, chiave, default=None):
        """Ottiene valore configurazione con fallback."""
        try:
            config = cls.objects.get(chiave_configurazione=chiave)
            return config.valore_configurazione
        except cls.DoesNotExist:
            return default


class InformazioniScuola(models.Model):
    """
    Informazioni complete sulla scuola.

    Singola istanza (singleton) con informazioni complete.
    """
    nome_completo_scuola = models.CharField(
        max_length=200,
        verbose_name='Nome Completo Scuola',
        help_text='Nome formale e completo della scuola'
    )
    nome_breve_scuola = models.CharField(
        max_length=100,
        verbose_name='Nome Breve Scuola',
        help_text='Nome abbreviato per interfaccia utente'
    )
    codice_meccanografico_scuola = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Codice Meccanografico',
        help_text='Codice ufficiale di identificazione'
    )
    partita_iva_scuola = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Partita IVA Scuola',
        help_text='Partita IVA della scuola'
    )
    sito_web_scuola = models.URLField(
        verbose_name='Sito Web Scuola',
        help_text='Sito web ufficiale della scuola'
    )
    email_istituzionale_scuola = models.EmailField(
        verbose_name='Email Istituzionale',
        help_text='Email principale della scuola'
    )
    telefono_scuola = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Telefono Scuola',
        help_text='Numero di telefono principale'
    )
    fax_scuola = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Fax Scuola'
    )

    # Indirizzo completo
    indirizzo_scuola = models.TextField(
        verbose_name='Indirizzo Completo Scuola',
        help_text='Indirizzo secondo standard Google Maps'
    )
    codice_postale_scuola = models.CharField(
        max_length=10,
        verbose_name='Codice Postale scuola',
        help_text='Codice di avviamento postale'
    )
    comune_scuola = models.CharField(
        max_length=100,
        verbose_name='Comune Scuola',
        help_text='Comune di appartenenza'
    )
    provincia_scuola = models.CharField(
        max_length=50,
        verbose_name='Provincia Scuola',
        help_text='Sigla provincia (es: GR, RM, MI)'
    )
    regione_scuola = models.CharField(
        max_length=50,
        verbose_name='Regione Scuola',
        help_text='Regione di appartenenza'
    )
    nazione_scuola = models.CharField(
        max_length=50,
        default='Italia',
        verbose_name='Nazione Scuola'
    )

    # Coordinate geografiche (per mappe)
    latitudine_scuola = models.DecimalField(
        max_digits=10, decimal_places=8,
        null=True, blank=True,
        verbose_name='Latitudine Scuola'
    )
    longitudine_scuola = models.DecimalField(
        max_digits=11, decimal_places=8,
        null=True, blank=True,
        verbose_name='Longitudine Scuola'
    )

    scuola_attiva = models.BooleanField(default=True)
    data_creazione_scuola = models.DateTimeField(auto_now_add=True)
    data_modifica_scuola = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Informazioni Scuola'
        verbose_name_plural = 'Informazioni Scuola'

    def __str__(self):
        return self.nome_breve_scuola or self.nome_completo_scuola

    @classmethod
    def ottieni_istanza(cls):
        """Ottiene l'unica istanza della scuola."""
        instance, creata = cls.objects.get_or_create(id=1)
        return instance

    @property
    def indirizzo_completo_scuola(self):
        """Indirizzo formattato completo."""
        return f"{self.indirizzo_scuola}, {self.codice_postale_scuola} {self.comune_scuola} ({self.provincia_scuola}), {self.regione_scuola}"


# =====================================================
# GESTIONE UTENTI AVANZATA
# =====================================================

class ProfiloUtente(models.Model):
    """
    Profilo esteso dell'utente.

    Complementa AbstractUser con informazioni aggiuntive.
    """
    SCELTE_SESSO = [
        ('M', 'Maschio'),
        ('F', 'Femmina'),
        ('ALTRO', 'Altro'),
    ]

    # Relazione 1:1 con User
    utente = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profilo_utente'
    )

    # Informazioni personali
    nome_utente = models.CharField(
        max_length=100,
        verbose_name='Nome Utente',
        help_text='Nome di battesimo'
    )
    cognome_utente = models.CharField(
        max_length=100,
        verbose_name='Cognome Utente',
        help_text='Cognome'
    )
    sesso_utente = models.CharField(
        max_length=10,
        choices=SCELTE_SESSO,
        blank=True,
        verbose_name='Sesso Utente'
    )
    data_nascita_utente = models.DateField(
        null=True, blank=True,
        verbose_name='Data Nascita Utente'
    )
    codice_fiscale_utente = models.CharField(
        max_length=16,
        blank=True,
        verbose_name='Codice Fiscale Utente'
    )

    # Contatti aggiuntivi
    telefono_utente = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Telefono Utente'
    )
    email_personale_utente = models.EmailField(
        blank=True,
        verbose_name='Email Personale Utente',
        help_text='Email alternativa per comunicazioni'
    )

    # Informazioni istituzionali
    numero_matricola_utente = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Numero Matricola Utente',
        help_text='Per studenti e docenti'
    )
    classe_utente = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Classe/Sezione Utente',
        help_text='Per studenti (es: 5A, 3B)'
    )
    dipartimento_utente = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Dipartimento Utente',
        help_text='Per docenti'
    )
    materia_insegnamento_utente = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Materia Insegnamento Utente',
        help_text='Per docenti'
    )

    # Preferenze sistema
    preferenze_notifica_utente = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Preferenze Notifica Utente',
        help_text='Configurazione notifiche personalizzate'
    )
    preferenze_lingua_utente = models.CharField(
        max_length=10,
        default='it',
        verbose_name='Lingua Preferita Utente'
    )
    fuso_orario_utente = models.CharField(
        max_length=50,
        default='Europe/Rome',
        verbose_name='Fuso Orario Utente'
    )

    # Stato e audit
    utente_attivo = models.BooleanField(default=True)
    utente_verificato = models.BooleanField(default=False)
    data_verifica_utente = models.DateTimeField(null=True, blank=True)
    ultimo_accesso_utente = models.DateTimeField(null=True, blank=True)

    data_creazione_utente = models.DateTimeField(auto_now_add=True)
    data_modifica_utente = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profilo Utente'
        verbose_name_plural = 'Profili Utenti'
        indexes = [
            models.Index(fields=['utente']),
            models.Index(fields=['utente_attivo']),
            models.Index(fields=['utente_verificato']),
        ]

    def __str__(self):
        return f"{self.nome_utente} {self.cognome_utente} ({self.utente.username})"

    @property
    def nome_completo_utente(self):
        return f"{self.nome_utente} {self.cognome_utente}"

    @property
    def eta_utente(self):
        if self.data_nascita_utente:
            oggi = timezone.now().date()
            return oggi.year - self.data_nascita_utente.year - (
                (oggi.month, oggi.day) < (self.data_nascita_utente.month, self.data_nascita_utente.day)
            )
        return None


# Nota: Rimuovendo il modello custom Utente per usare auth.User standard
# Tutti i campi aggiuntivi (ruolo, email_verificato, etc.) vengono spostati nel ProfiloUtente


# =====================================================
# GESTIONE SESSIONI E VERIFICHE
# =====================================================

class SessioneUtente(models.Model):
    """
    Gestione sessioni utente e stati di verifica.
    """
    TIPO_SESSIONE = [
        ('verifica_email', 'Verifica Email'),
        ('reset_password', 'Reset Password'),
        ('login_pin', 'Login con PIN'),
        ('setup_amministratore', 'Setup Amministratore'),
        ('conferma_prenotazione', 'Conferma Prenotazione'),
    ]

    TIPO_STATO = [
        ('in_attesa', 'In Attesa'),
        ('verificato', 'Verificato'),
        ('scaduto', 'Scaduto'),
        ('annullato', 'Annullato'),
        ('fallito', 'Fallito'),
    ]

    utente_sessione = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessioni_utente'
    )
    tipo_sessione = models.CharField(
        max_length=30,
        choices=TIPO_SESSIONE,
        verbose_name='Tipo Sessione'
    )
    token_sessione = models.UUIDField(
        default=genera_codice_univoco,
        unique=True,
        verbose_name='Token Sessone Unico'
    )
    pin_sessione = models.CharField(
        max_length=6,
        blank=True,
        verbose_name='PIN Sessione',
        help_text='Per verifiche PIN'
    )
    stato_sessione = models.CharField(
        max_length=20,
        choices=TIPO_STATO,
        default='in_attesa',
        verbose_name='Stato Sessione'
    )
    metadati_sessione = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadati Sessione',
        help_text='Dati aggiuntivi della sessione'
    )
    email_destinazione_sessione = models.EmailField(
        verbose_name='Email Destinazione Sessione'
    )

    data_creazione_sessione = models.DateTimeField(auto_now_add=True)
    data_scadenza_sessione = models.DateTimeField()
    data_verifica_sessione = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Sessione Utente'
        verbose_name_plural = 'Sessioni Utente'
        indexes = [
            models.Index(fields=['utente_sessione', 'tipo_sessione']),
            models.Index(fields=['token_sessione']),
            models.Index(fields=['stato_sessione']),
            models.Index(fields=['data_scadenza_sessione']),
        ]

    def __str__(self):
        return f"{self.utente_sessione.username} - {self.tipo_sessione} ({self.stato_sessione})"

    @property
    def sessione_scaduta(self):
        return timezone.now() > self.data_scadenza_sessione

    @property
    def sessione_valida(self):
        return self.stato_sessione == 'in_attesa' and not self.sessione_scaduta

    def verifica_sessione(self, pin=None):
        """Verifica la sessione con eventuale PIN."""
        if not self.sessione_valida:
            return False, "Sessione non valida o scaduta"

        if self.pin_sessione and pin != self.pin_sessione:
            return False, "PIN non corretto"

        self.stato_sessione = 'verificato'
        self.data_verifica_sessione = timezone.now()
        self.save()
        return True, "Verifica completata con successo"

    def scadenza_sessione(self):
        """Scadenza manuale della sessione."""
        self.stato_sessione = 'scaduto'
        self.save()
