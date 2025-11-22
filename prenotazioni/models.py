
from django.db.models.signals import post_migrate
from django.dispatch import receiver


# Pulizia automatica dei record ProfiloUtente dopo le migrazioni
import django
import logging
from django.db import connection
from django.db import ProgrammingError, OperationalError

@receiver(post_migrate)
def clean_profilo_utente_null_fields(sender, **kwargs):
    table_name = 'prenotazioni_profiloutente'
    with connection.cursor() as cursor:
        tables = connection.introspection.table_names()
    if table_name in tables:
        from .models import ProfiloUtente
        ProfiloUtente.objects.filter(nome_utente__isnull=True).update(nome_utente="")
        ProfiloUtente.objects.filter(cognome_utente__isnull=True).update(cognome_utente="")
# =====================================================
# SCELTE GLOBALI
# =====================================================

SCELTE_SESSO = [
    ('M', 'Maschio'),
    ('F', 'Femmina'),
    ('ALTRO', 'Altro'),
]
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
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.db.models.signals import post_save, post_delete


# =============================================================================
# UTENSILI AUSILIARI
# =============================================================================

def genera_codice_univoco():
    """Genera un codice univoco per elementi del sistema."""
    # Return a UUID instance (preferred for UUIDField defaults)
    return uuid.uuid4()


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

    data_creazione_sessione = models.DateTimeField(auto_now_add=True, verbose_name='Data Creazione Sessione')
    data_scadenza_sessione = models.DateTimeField(null=True, blank=True, verbose_name='Data Scadenza Sessione')
    data_verifica_sessione = models.DateTimeField(null=True, blank=True, verbose_name='Data Verifica Sessione')
    stato_sessione = models.CharField(max_length=20, choices=TIPO_STATO, default='in_attesa', verbose_name='Stato Sessione')
    metadati_sessione = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadati Sessione',
        help_text='Dati aggiuntivi della sessione'
    )
    email_destinazione_sessione = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email Destinazione Sessione',
        help_text='Email destinatario per notifiche o verifiche'
    )

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
    nome_utente = models.CharField(
        max_length=100,
        verbose_name='Nome Utente',
        help_text='Nome di battesimo',
        blank=True,
        null=True
    )
    cognome_utente = models.CharField(
        max_length=100,
        verbose_name='Cognome Utente',
        help_text='Cognome',
        blank=True,
        null=True
    )
    sesso_utente = models.CharField(
        max_length=10,
        choices=SCELTE_SESSO,
        blank=True,
        null=True,
        verbose_name='Sesso Utente'
    )
    data_nascita_utente = models.DateField(
        null=True, blank=True,
        verbose_name='Data Nascita Utente'
    )
    codice_fiscale_utente = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        verbose_name='Codice Fiscale Utente'
    )
    telefono_utente = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Telefono Utente'
    )
    email_personale_utente = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email Personale Utente',
        help_text='Email alternativa per comunicazioni'
    )
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


# =====================================================
# CATALOGO DISPOSITIVI
# =====================================================

class CategoriaDispositivo(models.Model):
    """
    Categorie di dispositivi per organizzazione gerarchica.
    """
    nome = models.CharField(max_length=100, unique=True, default="")
    descrizione = models.TextField(blank=True)
    icona = models.CharField(max_length=50, blank=True, help_text='Nome icona Bootstrap')
    colore = models.CharField(max_length=7, default='#007bff', help_text='Codice colore HEX')
    attiva = models.BooleanField(default=True)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Categoria Dispositivo'
        verbose_name_plural = 'Categorie Dispositivi'
        ordering = ['ordine', 'nome']

    def __str__(self):
        return self.nome


class UbicazioneRisorsa(models.Model):
    """
    Localizzazioni fisiche delle risorse.
    """
    nome = models.CharField(max_length=100, unique=True)
    descrizione = models.TextField(blank=True)
    edificio = models.CharField(max_length=50)
    piano = models.CharField(max_length=20)
    aula = models.CharField(max_length=50)
    capacita_persone = models.PositiveIntegerField(default=0)
    attrezzature_presenti = models.JSONField(default=list, blank=True)

    coordinate_x = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    coordinate_y = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    attivo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Localizzazione'
        verbose_name_plural = 'Localizzazioni'
        ordering = ['edificio', 'piano', 'aula']

    def __str__(self):
        return f"{self.edificio} - {self.piano} - {self.aula}"


class Dispositivo(models.Model):
    """
    Dispositivi disponibili nel sistema scolastico.
    """
    TIPO_DISPOSITIVO = [
        ('laptop', 'Laptop/Notebook'),
        ('desktop', 'Computer Desktop'),
        ('tablet', 'Tablet'),
        ('smartphone', 'Smartphone'),
        ('projector', 'Proiettore'),
        ('smartboard', 'Lavagna Interattiva'),
        ('camera', 'Videocamera'),
        ('audio', 'Attrezzatura Audio'),
        ('network', 'Attrezzatura Rete'),
        ('altro', 'Altro'),
    ]

    # Identificazione
    nome = models.CharField(max_length=100, verbose_name='Nome', default="")
    modello = models.CharField(max_length=100, blank=True)
    marca = models.CharField(max_length=100, verbose_name='Marca/Produttore')
    serie = models.CharField(max_length=100, blank=True, help_text='Numero di serie')
    codice_inventario = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Codice Inventario'
    )

    # Classificazione
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_DISPOSITIVO,
        verbose_name='Tipo Dispositivo'
    )
    categoria = models.ForeignKey(
        CategoriaDispositivo,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Specifiche tecniche
    specifiche = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Specifiche Tecniche',
        help_text='CPU, RAM, Storage, OS, etc.'
    )

    # Stato e disponibilità
    stato = models.CharField(
        max_length=20,
        default='disponibile',
        choices=[
            ('disponibile', 'Disponibile'),
            ('in_uso', 'In Uso'),
            ('manutenzione', 'In Manutenzione'),
            ('danneggiato', 'Danneggiato'),
            ('smarrito', 'Smarrito'),
            ('ritirato', 'Ritirato'),
        ]
    )
    attivo = models.BooleanField(default=True)

    # Localizzazione
    edificio = models.CharField(max_length=50, blank=True)
    piano = models.CharField(max_length=20, blank=True)
    aula = models.CharField(max_length=50, blank=True)
    armadio = models.CharField(max_length=50, blank=True)

    # Informazioni di acquisto
    data_acquisto = models.DateField(null=True, blank=True)
    data_scadenza_garanzia = models.DateField(null=True, blank=True)
    valore_acquisto = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )

    # Note e manutenzione
    note = models.TextField(blank=True)
    ultimo_controllo = models.DateTimeField(null=True, blank=True)
    prossima_manutenzione = models.DateTimeField(null=True, blank=True)

    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivi'
        ordering = ['tipo', 'marca', 'nome']
        indexes = [
            models.Index(fields=['codice_inventario']),
            models.Index(fields=['tipo', 'stato']),
            models.Index(fields=['categoria']),
            models.Index(fields=['attivo']),
        ]

    def __str__(self):
        if self.modello:
            return f"{self.marca} {self.nome} ({self.modello})"
        return f"{self.marca} {self.nome}"

    @property
    def display_name(self):
        return self.__str__()

    @property
    def is_available(self):
        return self.stato == 'disponibile' and self.attivo

    @property
    def needs_maintenance(self):
        if self.prossima_manutenzione:
            return timezone.now().date() >= self.prossima_manutenzione
        return False


# =====================================================
# RISORSE PRENOTABILI
# =====================================================

class Risorsa(models.Model):
    """
    Risorse prenotabili del sistema (laboratori, aule, carrelli, etc.).
    """
    TIPO_RISORSA = [
        ('laboratorio', 'Laboratorio'),
        ('aula', 'Aula'),
        ('carrello', 'Carrello Dispositivi'),
        ('spazio', 'Spazio Comune'),
        ('attrezzatura', 'Attrezzatura Speciale'),
        ('ambiente', 'Ambiente Esterno'),
    ]

    # Identificazione
    nome = models.CharField(max_length=100, verbose_name='Nome', default="")
    codice = models.CharField(max_length=20, unique=True, verbose_name='Codice')
    descrizione = models.TextField(blank=True)

    # Classificazione
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_RISORSA,
        verbose_name='Tipo Risorsa'
    )
    categoria = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Categoria'
    )

    # Localizzazione
    localizzazione = models.ForeignKey(
        UbicazioneRisorsa,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Capacità e specifiche
    capacita_massima = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Per carrelli: numero dispositivi max'
    )
    postazioni_disponibili = models.PositiveIntegerField(
        default=0,
        help_text='Numero postazioni fisiche'
    )

    # Dispositivi associati (per carrelli e laboratori)
    dispositivi = models.ManyToManyField(
        Dispositivo,
        blank=True,
        related_name='risorse',
        verbose_name='Dispositivi Associati'
    )

    # Orari e disponibilità
    orari_apertura = models.JSONField(
        default=dict,
        blank=True,
        help_text='Orari di disponibilità per giorno'
    )
    feriali_disponibile = models.BooleanField(default=True)
    weekend_disponibile = models.BooleanField(default=False)
    festivo_disponibile = models.BooleanField(default=False)

    # Stato
    attivo = models.BooleanField(default=True)
    manutenzione = models.BooleanField(default=False)
    bloccato = models.BooleanField(default=False)

    # Preferenze prenotazione
    prenotazione_anticipo_minimo = models.PositiveIntegerField(default=1)
    prenotazione_anticipo_massimo = models.PositiveIntegerField(default=30)
    durata_minima_minuti = models.PositiveIntegerField(default=30)
    durata_massima_minuti = models.PositiveIntegerField(default=240)

    # Gestione conflitti
    allow_overbooking = models.BooleanField(default=False)
    overbooking_limite = models.PositiveIntegerField(default=0)

    # Note
    note_amministrative = models.TextField(blank=True)
    note_utenti = models.TextField(blank=True)

    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Risorsa'
        verbose_name_plural = 'Risorse'
        ordering = ['tipo', 'nome']
        indexes = [
            models.Index(fields=['codice']),
            models.Index(fields=['tipo', 'attivo']),
            models.Index(fields=['localizzazione']),
            models.Index(fields=['attivo']),
            models.Index(fields=['manutenzione']),
            models.Index(fields=['bloccato']),
        ]

    def __str__(self):
        return f"{self.codice} - {self.nome}"

    def is_laboratorio(self):
        return self.tipo == 'laboratorio'

    def is_carrello(self):
        return self.tipo == 'carrello'

    def is_aula(self):
        return self.tipo == 'aula'

    def is_available_for_booking(self):
        return self.attivo and not self.manutenzione and not self.bloccato

    def get_available_devices(self):
        """Dispositivi disponibili nella risorsa."""
        return self.dispositivi.filter(attivo=True, stato='disponibile')


# =====================================================
# PRENOTAZIONI AVANZATE
# =====================================================

class StatoPrenotazione(models.Model):
    """
    Stati delle prenotazioni con workflow definito.
    """
    nome = models.CharField(max_length=50, unique=True)
    descrizione = models.TextField()
    colore = models.CharField(max_length=7, default='#007bff')
    icon = models.CharField(max_length=50, blank=True)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Stato Prenotazione'
        verbose_name_plural = 'Stati Prenotazioni'
        ordering = ['ordine']

    def __str__(self):
        return self.nome


class Prenotazione(models.Model):
    """
    Prenotazione di risorse con workflow avanzato.
    """
    PRIORITA = [
        ('bassa', 'Bassa'),
        ('normale', 'Normale'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    # Relazioni principali
    utente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='prenotazioni'
    )
    risorsa = models.ForeignKey(
        Risorsa,
        on_delete=models.CASCADE,
        related_name='prenotazioni'
    )

    # Dispositivi specifici (per carrelli)
    dispositivi_selezionati = models.ManyToManyField(
        Dispositivo,
        blank=True,
        related_name='prenotazioni',
        verbose_name='Dispositivi Specifici'
    )

    # Dettagli prenotazione
    inizio = models.DateTimeField(verbose_name='Inizio')
    fine = models.DateTimeField(verbose_name='Fine')
    quantita = models.PositiveIntegerField(default=1)
    priorita = models.CharField(
        max_length=20,
        choices=PRIORITA,
        default='normale'
    )

    # Stato e workflow
    stato = models.ForeignKey(
        StatoPrenotazione,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Informazioni aggiuntive
    scopo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Scopo della prenotazione'
    )
    note = models.TextField(blank=True)
    note_amministrative = models.TextField(blank=True)

    # Configurazione speciale
    setup_needed = models.BooleanField(
        default=False,
        help_text='Richiede setup/assistenza tecnica'
    )
    cleanup_needed = models.BooleanField(
        default=False,
        help_text='Richiede pulizia/riordino'
    )

    # Validazione e conformità
    approvazione_richiesta = models.BooleanField(default=False)
    approvato_da = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='prenotazioni_approvate'
    )
    data_approvazione = models.DateTimeField(null=True, blank=True)

    # Notifiche
    notifiche_inviate = models.JSONField(default=list, blank=True)
    ultimo_aggiornamento_notifica = models.DateTimeField(null=True, blank=True)

    # Audit trail
    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)
    cancellato_il = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Prenotazione'
        verbose_name_plural = 'Prenotazioni'
        ordering = ['-inizio']
        indexes = [
            models.Index(fields=['utente', 'inizio']),
            models.Index(fields=['risorsa', 'inizio', 'fine']),
            models.Index(fields=['stato']),
            models.Index(fields=['inizio', 'fine']),
        ]

    def __str__(self):
        return f"{self.utente.username} - {self.risorsa.nome} ({self.inizio.strftime('%d/%m/%Y %H:%M')})"

    def cancel(self, user, reason=""):
        """Cancella la prenotazione."""
        if not self.can_be_cancelled_by(user):
            return False, "Non hai i permessi per cancellare questa prenotazione"

        self.cancellato_il = timezone.now()

        cancelled_status = StatoPrenotazione.objects.get_or_create(
            nome='cancelled',
            defaults={'descrizione': 'Cancellata', 'colore': '#dc3545'}
        )[0]
        self.stato = cancelled_status

        if reason:
            self.note_amministrative += f"\nCancellata da {user.username}: {reason}"

        self.save()
        return True, "Prenotazione cancellata con successo"


# =====================================================
# SISTEMA DI LOG E MONITORAGGIO
# =====================================================

class LogSistema(models.Model):
    """
    Log del sistema per audit e debugging.
    """
    LIVELLO_LOG = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Informazione'),
        ('WARNING', 'Avviso'),
        ('ERROR', 'Errore'),
        ('CRITICAL', 'Critico'),
    ]

    livello = models.CharField(
        max_length=10,
        choices=LIVELLO_LOG,
        default='INFO'
    )
    tipo_evento = models.CharField(max_length=30)
    utente = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='logs'
    )

    messaggio = models.TextField(verbose_name='Messaggio')
    dettagli = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log Sistema'
        verbose_name_plural = 'Log Sistema'
        ordering = ['-timestamp']

    def __str__(self):
        user_info = self.utente.username if self.utente else "Sistema"
        return f"[{self.livello}] {user_info}: {self.messaggio[:50]}..."


class TemplateNotifica(models.Model):
    """
    Template per notifiche email e sistema.
    """
    TIPO_NOTIFICA = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Notifica Push'),
        ('in_app', 'In-App'),
    ]

    nome = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_NOTIFICA)
    evento = models.CharField(max_length=50, help_text='Evento che triggera la notifica')

    oggetto = models.CharField(max_length=200, help_text='Per email/SMS')
    contenuto = models.TextField(help_text='Template con variabili {{variable}}')

    attivo = models.BooleanField(default=True)
    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Template Notifica'
        verbose_name_plural = 'Template Notifiche'

    def render_template(self, context):
        """Rende il template con il context fornito."""
        from string import Template
        try:
            template = Template(self.contenuto)
            return template.safe_substitute(context)
        except Exception as e:
            return f"Errore rendering template: {e}"


class NotificaUtente(models.Model):
    """
    Notifiche inviate nel sistema.
    """
    STATO_NOTIFICA = [
        ('pending', 'In Coda'),
        ('sent', 'Inviata'),
        ('delivered', 'Consegnata'),
        ('failed', 'Fallita'),
        ('cancelled', 'Annullata'),
    ]

    utente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifiche'
    )
    template = models.ForeignKey(
        TemplateNotifica,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    tipo = models.CharField(max_length=20)
    canale = models.CharField(max_length=20)

    titolo = models.CharField(max_length=200, blank=True)
    messaggio = models.TextField()
    dati_aggiuntivi = models.JSONField(default=dict, blank=True)

    stato = models.CharField(
        max_length=20,
        choices=STATO_NOTIFICA,
        default='pending'
    )
    tentativo_corrente = models.PositiveIntegerField(default=0)
    ultimo_tentativo = models.DateTimeField(null=True, blank=True)
    prossimo_tentativo = models.DateTimeField(null=True, blank=True)

    inviata_il = models.DateTimeField(null=True, blank=True)
    consegnata_il = models.DateTimeField(null=True, blank=True)
    errore_messaggio = models.TextField(blank=True)

    related_booking = models.ForeignKey(
        Prenotazione,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    related_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifiche_riferimento'
    )

    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notifica'
        verbose_name_plural = 'Notifiche'
        ordering = ['-creato_il']

    def __str__(self):
        return f"{self.utente.username} - {self.tipo} ({self.stato})"


# =====================================================
# FILE E ALLEGATI
# =====================================================

class CaricamentoFile(models.Model):
    """
    Gestione file e allegati nel sistema.
    """
    TIPO_FILE = [
        ('document', 'Documento'),
        ('image', 'Immagine'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('archive', 'Archivio'),
        ('other', 'Altro'),
    ]

    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    nome_originale = models.CharField(max_length=255)
    dimensione = models.PositiveIntegerField(help_text='Dimensione in bytes')
    tipo_mime = models.CharField(max_length=100)
    tipo_file = models.CharField(max_length=20, choices=TIPO_FILE)

    titolo = models.CharField(max_length=200, blank=True)
    descrizione = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    checksum = models.CharField(max_length=64, blank=True, help_text='SHA256 hash')
    virus_scanned = models.BooleanField(default=False)
    scan_result = models.CharField(max_length=20, blank=True)

    caricato_da = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='file_caricati'
    )

    pubblico = models.BooleanField(default=False)
    attivo = models.BooleanField(default=True)

    download_count = models.PositiveIntegerField(default=0)
    ultimo_download = models.DateTimeField(null=True, blank=True)

    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'File Caricato'
        verbose_name_plural = 'File Caricati'
        ordering = ['-creato_il']

    def __str__(self):
        return self.nome_originale


# =====================================================
# FUNZIONI HELPER
# =====================================================

def log_user_action(user, action_type, message, **kwargs):
    """Helper per loggare azioni utente."""
    return LogSistema.objects.create(
        tipo_evento=action_type,
        messaggio=message,
        utente=user,
        **kwargs
    )


def create_notification(user, template_name, context, **kwargs):
    """Helper per creare notifiche."""
    try:
        template = TemplateNotifica.objects.get(nome=template_name, attivo=True)
        rendered_message = template.render_template(context)
        rendered_title = template.render_template({'title': template.oggetto, **context})

        return NotificaUtente.objects.create(
            utente=user,
            template=template,
            tipo=template.evento,
            canale=template.tipo,
            titolo=rendered_title,
            messaggio=rendered_message,
            dati_aggiuntivi=context,
            **kwargs
        )
    except TemplateNotifica.DoesNotExist:
        return None



# =====================================================
# SEGNALI (SIGNALS)
# =====================================================

def create_user_profile_signal(sender, instance, created, **kwargs):
    """Crea profilo automaticamente quando viene creato un utente."""
    if created:
        # Valorizza i campi obbligatori con dati di User o stringa vuota
        try:
            ProfiloUtente.objects.create(
                utente=instance,
                nome_utente=getattr(instance, 'first_name', '') or '',
                cognome_utente=getattr(instance, 'last_name', '') or ''
            )
        except (ProgrammingError, OperationalError) as e:
            logger = logging.getLogger('prenotazioni')
            logger.error('Could not create ProfiloUtente on user creation (db not ready?): %s', e)
            # Silently skip profile creation when DB/table isn't available yet.
            return


def save_user_profile_signal(sender, instance, **kwargs):
    """Salva profilo quando viene salvato l'utente."""
    # Il related_name usato nel modello è `profilo_utente`
    if hasattr(instance, 'profilo_utente') and instance.profilo_utente:
        instance.profilo_utente.save()


def log_booking_action_signal(sender, instance, created, **kwargs):
    """Log azioni prenotazioni."""
    if created:
        # Usa il nostro helper di log passando i campi corretti
        try:
            log_user_action(
                user=instance.utente if hasattr(instance, 'utente') else None,
                action_type='booking_created',
                message=f"Prenotazione creata: {getattr(instance.risorsa, 'nome', '')}",
                related_booking=instance
            )
        except Exception:
            # Non bloccare il flusso se il logging fallisce
            pass

def log_booking_deletion_signal(sender, instance, **kwargs):
    """Log cancellazione prenotazioni."""
    log_user_action(
        utente=instance.utente,
        action_type='booking_cancelled',
        message=f"Prenotazione cancellata: {instance.risorsa.nome}",
        related_booking=instance
    )


# Signals essenziali: solo creazione profilo utente
post_save.connect(create_user_profile_signal, sender=User)
