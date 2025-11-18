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
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid


# =====================================================
# CONFIGURAZIONE E SETTINGS
# =====================================================

class Configuration(models.Model):
    """
    Configurazione centralizzata del sistema.
    
    Sostituisce settings.py dispersi con configurazione database-driven.
    """
    TIPO_CONFIG = [
        ('email', 'Email/SMTP'),
        ('booking', 'Prenotazioni'),
        ('system', 'Sistema'),
        ('ui', 'Interfaccia'),
        ('security', 'Sicurezza'),
    ]
    
    chiave = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Chiave configurazione',
        help_text='Identificatore univoco (es: EMAIL_HOST, BOOKING_START_HOUR)'
    )
    valore = models.TextField(
        verbose_name='Valore',
        help_text='Valore della configurazione'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CONFIG,
        verbose_name='Tipo configurazione',
        help_text='Categoria della configurazione'
    )
    descrizione = models.TextField(
        blank=True,
        verbose_name='Descrizione',
        help_text='Descrizione della configurazione'
    )
    modificabile = models.BooleanField(
        default=True,
        verbose_name='Modificabile',
        help_text='Se la configurazione può essere modificata da admin'
    )
    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configurazione'
        verbose_name_plural = 'Configurazioni'
        ordering = ['tipo', 'chiave']
    
    def __str__(self):
        return f"{self.chiave}: {self.valore[:50]}..."
    
    @classmethod
    def get_config(cls, chiave, default=None):
        """Ottiene valore configurazione con fallback."""
        try:
            config = cls.objects.get(chiave=chiave)
            return config.valore
        except cls.DoesNotExist:
            return default


class SchoolInfo(models.Model):
    """
    Informazioni complete sulla scuola.
    
    Singola istanza (singleton) con informazioni complete.
    """
    nome_completo = models.CharField(
        max_length=200,
        verbose_name='Nome completo scuola',
        help_text='Nome formale e completo della scuola'
    )
    nome_breve = models.CharField(
        max_length=100,
        verbose_name='Nome breve',
        help_text='Nome abbreviato per interfaccia utente'
    )
    codice_meccanografico = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Codice meccanografico',
        help_text='Codice ufficiale di identificazione'
    )
    partita_iva = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Partita IVA',
        help_text='Partita IVA della scuola'
    )
    sito_web = models.URLField(
        verbose_name='URL sito web',
        help_text='Sito web ufficiale della scuola'
    )
    email_istituzionale = models.EmailField(
        verbose_name='Email istituzionale',
        help_text='Email principale della scuola'
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Telefono',
        help_text='Numero di telefono principale'
    )
    fax = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Fax'
    )
    
    # Indirizzo completo
    indirizzo = models.TextField(
        verbose_name='Indirizzo completo',
        help_text='Indirizzo secondo standard Google Maps'
    )
    cap = models.CharField(
        max_length=10,
        verbose_name='CAP',
        help_text='Codice di avviamento postale'
    )
    comune = models.CharField(
        max_length=100,
        verbose_name='Comune',
        help_text='Comune di appartenenza'
    )
    provincia = models.CharField(
        max_length=50,
        verbose_name='Provincia',
        help_text='Sigla provincia (es: GR, RM, MI)'
    )
    regione = models.CharField(
        max_length=50,
        verbose_name='Regione',
        help_text='Regione di appartenenza'
    )
    nazione = models.CharField(
        max_length=50,
        default='Italia',
        verbose_name='Nazione'
    )
    
    # Coordinata geografiche (per mappe)
    latitudine = models.DecimalField(
        max_digits=10, decimal_places=8,
        null=True, blank=True,
        verbose_name='Latitudine'
    )
    longitudine = models.DecimalField(
        max_digits=11, decimal_places=8,
        null=True, blank=True,
        verbose_name='Longitudine'
    )
    
    attivo = models.BooleanField(default=True)
    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Informazioni Scuola'
        verbose_name_plural = 'Informazioni Scuola'
    
    def __str__(self):
        return self.nome_breve or self.nome_completo
    
    @classmethod
    def get_instance(cls):
        """Ottiene l'unica istanza della scuola."""
        instance, created = cls.objects.get_or_create(id=1)
        return instance
    
    @property
    def indirizzo_completo(self):
        """Indirizzo formattato completo."""
        return f"{self.indirizzo}, {self.cap} {self.comune} ({self.provincia}), {self.regione}"


# =====================================================
# GESTIONE UTENTI AVANZATA
# =====================================================

class UserProfile(models.Model):
    """
    Profilo esteso dell'utente.
    
    Complementa AbstractUser con informazioni aggiuntive.
    """
    SESSO_CHOICES = [
        ('M', 'Maschio'),
        ('F', 'Femmina'),
        ('ALTRO', 'Altro'),
    ]
    
    # Relazione 1:1 con User
    user = models.OneToOneField(
        'prenotazioni.Utente',
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Informazioni personali
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome',
        help_text='Nome di battesimo'
    )
    cognome = models.CharField(
        max_length=100,
        verbose_name='Cognome',
        help_text='Cognome'
    )
    sesso = models.CharField(
        max_length=10,
        choices=SESSO_CHOICES,
        blank=True,
        verbose_name='Sesso'
    )
    data_nascita = models.DateField(
        null=True, blank=True,
        verbose_name='Data di nascita'
    )
    codice_fiscale = models.CharField(
        max_length=16,
        blank=True,
        verbose_name='Codice Fiscale'
    )
    
    # Contatti aggiuntivi
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Telefono'
    )
    email_personale = models.EmailField(
        blank=True,
        verbose_name='Email personale',
        help_text='Email alternativa per comunicazioni'
    )
    
    # Informazioni istituzionali
    numero_matricola = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Numero Matricola',
        help_text='Per studenti e docenti'
    )
    classe = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Classe/Sezione',
        help_text='Per studenti (es: 5A, 3B)'
    )
    dipartimento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Dipartimento',
        help_text='Per docenti'
    )
    materia_insegnamento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Materia insegnamento',
        help_text='Per docenti'
    )
    
    # Preferenze sistema
    preferenze_notifica = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Preferenze Notifiche',
        help_text='Configurazione notifiche personalizzate'
    )
    preferenze_lingua = models.CharField(
        max_length=10,
        default='it',
        verbose_name='Lingua Preferita'
    )
    fuso_orario = models.CharField(
        max_length=50,
        default='Europe/Rome',
        verbose_name='Fuso Orario'
    )
    
    # Stato e audit
    attivo = models.BooleanField(default=True)
    verificato = models.BooleanField(default=False)
    data_verifica = models.DateTimeField(null=True, blank=True)
    ultimo_accesso = models.DateTimeField(null=True, blank=True)
    
    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Profilo Utente'
        verbose_name_plural = 'Profili Utenti'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['attivo']),
            models.Index(fields=['verificato']),
        ]
    
    def __str__(self):
        return f"{self.nome} {self.cognome} ({self.user.username})"
    
    @property
    def nome_completo(self):
        return f"{self.nome} {self.cognome}"
    
    @property
    def eta(self):
        if self.data_nascita:
            today = timezone.now().date()
            return today.year - self.data_nascita.year - (
                (today.month, today.day) < (self.data_nascita.month, self.data_nascita.day)
            )
        return None


class Utente(AbstractUser):
    """
    Utente esteso del sistema.
    
    Mantiene compatibilità con Django auth aggiungendo ruoli e funzionalità.
    """
    RUOLI = [
        ('studente', 'Studente'),
        ('docente', 'Docente'),
        ('assistente', 'Assistente Tecnico'),
        ('coordinatore', 'Coordinatore'),
        ('amministrativo', 'Personale Amministrativo'),
        ('admin', 'Amministratore'),
    ]
    
    ruolo = models.CharField(
        max_length=20,
        choices=RUOLI,
        default='studente',
        verbose_name='Ruolo',
        help_text='Ruolo principale nel sistema scolastico'
    )
    
    # Campo email deve essere unico
    email = models.EmailField(unique=True)
    
    # Stato account
    email_verificato = models.BooleanField(default=False)
    telefono_verificato = models.BooleanField(default=False)
    account_attivo = models.BooleanField(default=True)
    
    # Gestione PIN e sessioni
    pin_tentativi = models.PositiveIntegerField(default=0)
    ultimo_pin_tentativo = models.DateTimeField(null=True, blank=True)
    pin_bloccato_fino = models.DateTimeField(null=True, blank=True)
    
    # Audit
    ultimo_login_ip = models.GenericIPAddressField(null=True, blank=True)
    data_creazione = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Utente'
        verbose_name_plural = 'Utenti'
        indexes = [
            models.Index(fields=['ruolo']),
            models.Index(fields=['email_verificato']),
            models.Index(fields=['account_attivo']),
        ]
    
    def __str__(self):
        return self.username
    
    def is_docente(self):
        return self.ruolo == 'docente'
    
    def is_studente(self):
        return self.ruolo == 'studente'
    
    def is_assistente(self):
        return self.ruolo == 'assistente'
    
    def is_coordinatore(self):
        return self.ruolo == 'coordinatore'
    
    def is_amministrativo(self):
        return self.ruolo == 'amministrativo'
    
    def is_admin(self):
        return self.ruolo == 'admin'
    
    def can_book(self):
        """Verifica se l'utente può effettuare prenotazioni."""
        return self.account_attivo and self.email_verificato and self.is_authenticated
    
    def is_blocked(self):
        """Verifica se l'account è temporaneamente bloccato."""
        if self.pin_bloccato_fino:
            return timezone.now() < self.pin_bloccato_fino
        return False
    
    def increment_pin_attempts(self):
        """Incrementa i tentativi PIN e applica blocco se necessario."""
        self.pin_tentativi += 1
        if self.pin_tentativi >= 5:  # Massimo 5 tentativi
            from django.utils import timezone as tz
            self.pin_bloccato_fino = tz.now() + timezone.timedelta(hours=1)
        self.ultimo_pin_tentativo = timezone.now()
        self.save()


# =====================================================
# GESTIONE SESSIONI E VERIFICHE
# =====================================================

class UserSession(models.Model):
    """
    Gestione sessioni utente e stati di verifica.
    """
    TIPO_SESSIONE = [
        ('email_verification', 'Verifica Email'),
        ('password_reset', 'Reset Password'),
        ('pin_login', 'Login con PIN'),
        ('admin_setup', 'Setup Amministratore'),
        ('booking_confirmation', 'Conferma Prenotazione'),
    ]
    
    TIPO_STATO = [
        ('pending', 'In Attesa'),
        ('verified', 'Verificato'),
        ('expired', 'Scaduto'),
        ('cancelled', 'Annullato'),
        ('failed', 'Fallito'),
    ]
    
    user = models.ForeignKey(
        Utente,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_SESSIONE,
        verbose_name='Tipo Sessione'
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name='Token Unico'
    )
    pin = models.CharField(
        max_length=6,
        blank=True,
        verbose_name='PIN',
        help_text='Per verifiche PIN'
    )
    stato = models.CharField(
        max_length=20,
        choices=TIPO_STATO,
        default='pending',
        verbose_name='Stato'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadati',
        help_text='Dati aggiuntivi della sessione'
    )
    email_destinazione = models.EmailField(
        verbose_name='Email Destinazione'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Sessione Utente'
        verbose_name_plural = 'Sessioni Utente'
        indexes = [
            models.Index(fields=['user', 'tipo']),
            models.Index(fields=['token']),
            models.Index(fields=['stato']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.tipo} ({self.stato})"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return self.stato == 'pending' and not self.is_expired
    
    def verify(self, pin=None):
        """Verifica la sessione con eventuale PIN."""
        if not self.is_valid:
            return False, "Sessione non valida o scaduta"
        
        if self.pin and pin != self.pin:
            return False, "PIN non corretto"
        
        self.stato = 'verified'
        self.verified_at = timezone.now()
        self.save()
        return True, "Verifica completata con successo"
    
    def expire(self):
        """Scadenza manuale della sessione."""
        self.stato = 'expired'
        self.save()


# =====================================================
# CATALOGO DISPOSITIVI
# =====================================================

class DeviceCategory(models.Model):
    """
    Categorie di dispositivi per organizzazione gerarchica.
    """
    nome = models.CharField(max_length=100, unique=True)
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


class Device(models.Model):
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
    nome = models.CharField(max_length=100, verbose_name='Nome')
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
        DeviceCategory,
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
        constraints = [
            models.UniqueConstraint(
                fields=['marca', 'nome', 'modello'],
                name='unique_device_specs'
            ),
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

class ResourceLocation(models.Model):
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


class Resource(models.Model):
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
    nome = models.CharField(max_length=100, verbose_name='Nome')
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
        ResourceLocation,
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
        Device,
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
    
    def get_booked_devices_in_period(self, start, end):
        """Dispositivi prenotati nel periodo specificato."""
        from django.db.models import Sum
        # Implementazione della logica di prenotazione dispositivi
        return self.dispositivi.none()  # Placeholder


# =====================================================
# PRENOTAZIONI AVANZATE
# =====================================================

class BookingStatus(models.Model):
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


class Booking(models.Model):
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
        Utente,
        on_delete=models.CASCADE,
        related_name='prenotazioni'
    )
    risorsa = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='prenotazioni'
    )
    
    # Dispositivi specifici (per carrelli)
    dispositivi_selezionati = models.ManyToManyField(
        Device,
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
        BookingStatus,
        on_delete=models.SET_NULL,
        null=True,
        default=lambda: BookingStatus.objects.get_or_create(
            nome='pending',
            defaults={'descrizione': 'In Attesa', 'colore': '#ffc107'}
        )[0]
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
        Utente,
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
        constraints = [
            models.CheckConstraint(
                check=models.Q(fine__gt=models.F('inizio')),
                name='valid_date_range'
            ),
            models.CheckConstraint(
                check=models.Q(quantita__gt=0),
                name='positive_quantity'
            ),
        ]
    
    def __str__(self):
        return f"{self.utente.username} - {self.risorsa.nome} ({self.inizio.strftime('%d/%m/%Y %H:%M')})"
    
    @property
    def durata_minuti(self):
        return int((self.fine - self.inizio).total_seconds() // 60)
    
    @property
    def durata_ore(self):
        return round((self.fine - self.inizio).total_seconds() / 3600, 2)
    
    def is_passata(self):
        return self.fine < timezone.now()
    
    def is_futura(self):
        return self.inizio > timezone.now()
    
    def is_in_corso(self):
        now = timezone.now()
        return self.inizio <= now <= self.fine
    
    def sovrappone_con(self, other):
        """Verifica sovrapposizione con un'altra prenotazione."""
        return (self.inizio < other.fine and self.fine > other.inizio)
    
    def can_be_modified_by(self, user):
        """Verifica se l'utente può modificare questa prenotazione."""
        if user.is_admin():
            return True
        return self.utente == user and self.is_futura()
    
    def can_be_cancelled_by(self, user):
        """Verifica se l'utente può cancellare questa prenotazione."""
        if user.is_admin():
            return True
        return self.utente == user
    
    def approve(self, approver):
        """Approva la prenotazione."""
        self.approvato_da = approver
        self.data_approvazione = timezone.now()
        self.approvazione_richiesta = False
        
        # Cambia stato se necessario
        if self.stato and self.stato.nome == 'pending_approval':
            approved_status = BookingStatus.objects.get_or_create(
                nome='approved',
                defaults={'descrizione': 'Approvata', 'colore': '#28a745'}
            )[0]
            self.stato = approved_status
        
        self.save()
    
    def cancel(self, user, reason=""):
        """Cancella la prenotazione."""
        if not self.can_be_cancelled_by(user):
            return False, "Non hai i permessi per cancellare questa prenotazione"
        
        self.cancellato_il = timezone.now()
        
        # Imposta stato cancellato
        cancelled_status = BookingStatus.objects.get_or_create(
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

class SystemLog(models.Model):
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
    
    TIPO_EVENTO = [
        ('user_login', 'Login Utente'),
        ('user_logout', 'Logout Utente'),
        ('user_registration', 'Registrazione'),
        ('booking_created', 'Prenotazione Creata'),
        ('booking_modified', 'Prenotazione Modificata'),
        ('booking_cancelled', 'Prenotazione Cancellata'),
        ('booking_approved', 'Prenotazione Approvata'),
        ('device_assigned', 'Dispositivo Assegnato'),
        ('resource_created', 'Risorsa Creata'),
        ('config_changed', 'Configurazione Modificata'),
        ('system_error', 'Errore Sistema'),
        ('security_event', 'Eventi Sicurezza'),
        ('email_sent', 'Email Inviata'),
        ('data_export', 'Esportazione Dati'),
        ('backup_created', 'Backup Creato'),
    ]
    
    livello = models.CharField(
        max_length=10,
        choices=LIVELLO_LOG,
        default='INFO'
    )
    tipo_evento = models.CharField(max_length=30, choices=TIPO_EVENTO)
    utente = models.ForeignKey(
        Utente,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='logs'
    )
    
    # Dettagli evento
    messaggio = models.TextField(verbose_name='Messaggio')
    dettagli = models.JSONField(default=dict, blank=True)
    
    # Contesto tecnico
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=200, blank=True)
    metodo_http = models.CharField(max_length=10, blank=True)
    
    # Riferimenti oggetti
    object_type = models.CharField(max_length=50, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log Sistema'
        verbose_name_plural = 'Log Sistema'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['utente', 'timestamp']),
            models.Index(fields=['tipo_evento', 'timestamp']),
            models.Index(fields=['livello', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        user_info = self.utente.username if self.utente else "Sistema"
        return f"[{self.livello}] {user_info}: {self.messaggio[:50]}..."
    
    @classmethod
    def log_event(cls, tipo_evento, messaggio, livello='INFO', utente=None, 
                  dettagli=None, ip_address=None, **kwargs):
        """Crea rapidamente un log event."""
        return cls.objects.create(
            tipo_evento=tipo_evento,
            messaggio=messaggio,
            livello=livello,
            utente=utente,
            dettagli=dettagli or {},
            ip_address=ip_address,
            **kwargs
        )


class NotificationTemplate(models.Model):
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
    
    # Contenuto
    oggetto = models.CharField(max_length=200, help_text='Per email/SMS')
    contenuto = models.TextField(help_text='Template con variabili {{variable}}')
    
    # Configurazione
    attivo = models.BooleanField(default=True)
    invio_immediato = models.BooleanField(default=True)
    tentativi_massimi = models.PositiveIntegerField(default=3)
    intervallo_tentativi_minuti = models.PositiveIntegerField(default=15)
    
    # Variabili disponibili
    variabili_disponibili = models.JSONField(default=list)
    
    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Template Notifica'
        verbose_name_plural = 'Template Notifiche'
    
    def __str__(self):
        return self.nome
    
    def render_template(self, context):
        """Rende il template con il context fornito."""
        from string import Template
        try:
            template = Template(self.contenuto)
            return template.safe_substitute(context)
        except Exception as e:
            return f"Errore rendering template: {e}"


class Notification(models.Model):
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
        Utente,
        on_delete=models.CASCADE,
        related_name='notifiche'
    )
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    tipo = models.CharField(max_length=20)
    canale = models.CharField(max_length=20)  # email, sms, push, in_app
    
    # Contenuto
    titolo = models.CharField(max_length=200, blank=True)
    messaggio = models.TextField()
    dati_aggiuntivi = models.JSONField(default=dict, blank=True)
    
    # Stato e tracking
    stato = models.CharField(
        max_length=20,
        choices=STATO_NOTIFICA,
        default='pending'
    )
    tentativo_corrente = models.PositiveIntegerField(default=0)
    ultimo_tentativo = models.DateTimeField(null=True, blank=True)
    prossimo_tentativo = models.DateTimeField(null=True, blank=True)
    
    # Tracking consegna
    inviata_il = models.DateTimeField(null=True, blank=True)
    consegnata_il = models.DateTimeField(null=True, blank=True)
    errore_messaggio = models.TextField(blank=True)
    
    # Riferimenti
    related_booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    related_user = models.ForeignKey(
        Utente,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifiche_riferimento'
    )
    
    creato_il = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notifica'
        verbose_name_plural = 'Notifiche'
        ordering = ['-creato_il']
        indexes = [
            models.Index(fields=['utente', 'stato']),
            models.Index(fields=['tipo', 'stato']),
            models.Index(fields=['creato_il']),
        ]
    
    def __str__(self):
        return f"{self.utente.username} - {self.tipo} ({self.stato})"
    
    @property
    def is_pending(self):
        return self.stato == 'pending'
    
    @property
    def can_retry(self):
        return self.stato in ['failed', 'pending'] and self.tentativo_corrente < (
            self.template.tentativi_massimi if self.template else 3
        )


# =====================================================
# FILE E ALLEGATI
# =====================================================

class FileUpload(models.Model):
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
    
    # File
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    nome_originale = models.CharField(max_length=255)
    dimensione = models.PositiveIntegerField(help_text='Dimensione in bytes')
    tipo_mime = models.CharField(max_length=100)
    tipo_file = models.CharField(max_length=20, choices=TIPO_FILE)
    
    # Metadati
    titolo = models.CharField(max_length=200, blank=True)
    descrizione = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Sicurezza e validazione
    checksum = models.CharField(max_length=64, blank=True, help_text='SHA256 hash')
    virus_scanned = models.BooleanField(default=False)
    scan_result = models.CharField(max_length=20, blank=True)
    
    # Relazioni
    caricato_da = models.ForeignKey(
        Utente,
        on_delete=models.SET_NULL,
        null=True,
        related_name='file_caricati'
    )
    
    # Stati
    pubblico = models.BooleanField(default=False)
    attivo = models.BooleanField(default=True)
    
    # Accesso e download
    download_count = models.PositiveIntegerField(default=0)
    ultimo_download = models.DateTimeField(null=True, blank=True)
    
    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'File Caricato'
        verbose_name_plural = 'File Caricati'
        ordering = ['-creato_il']
        indexes = [
            models.Index(fields=['caricato_da', 'creato_il']),
            models.Index(fields=['tipo_file']),
            models.Index(fields=['pubblico', 'attivo']),
        ]
    
    def __str__(self):
        return self.nome_originale
    
    @property
    def estensione(self):
        return self.nome_originale.split('.')[-1].lower() if '.' in self.nome_originale else ''
    
    @property
    def dimensione_formattata(self):
        """Dimensione formattata in formato leggibile."""
        size = self.dimensione
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def increment_download(self):
        """Incrementa contatore download."""
        self.download_count += 1
        self.ultimo_download = timezone.now()
        self.save()


# =====================================================
# FUNZIONI HELPER
# =====================================================

def log_user_action(user, action_type, message, **kwargs):
    """Helper per loggare azioni utente."""
    return SystemLog.log_event(
        tipo_evento=action_type,
        messaggio=message,
        utente=user,
        **kwargs
    )


def create_notification(user, template_name, context, **kwargs):
    """Helper per creare notifiche."""
    try:
        template = NotificationTemplate.objects.get(nome=template_name, attivo=True)
        rendered_message = template.render_template(context)
        rendered_title = template.render_template({'title': template.oggetto, **context})
        
        return Notification.objects.create(
            utente=user,
            template=template,
            tipo=template.evento,
            canale=template.tipo,
            titolo=rendered_title,
            messaggio=rendered_message,
            dati_aggiuntivi=context,
            **kwargs
        )
    except NotificationTemplate.DoesNotExist:
        return None


# =====================================================
# SEGNALI (SIGNALS)
# =====================================================

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=Utente)
def create_user_profile(sender, instance, created, **kwargs):
    """Crea profilo automaticamente quando viene creato un utente."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=Utente)
def save_user_profile(sender, instance, **kwargs):
    """Salva profilo quando viene salvato l'utente."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=Booking)
def log_booking_action(sender, instance, created, **kwargs):
    """Log azioni prenotazioni."""
    if created:
        log_user_action(
            utente=instance.utente,
            action_type='booking_created',
            message=f"Prenotazione creata: {instance.risorsa.nome}",
            related_booking=instance
        )
    else:
        log_user_action(
            utente=instance.utente,
            action_type='booking_modified',
            message=f"Prenotazione modificata: {instance.risorsa.nome}",
            related_booking=instance
        )


@receiver(post_delete, sender=Booking)
def log_booking_deletion(sender, instance, **kwargs):
    """Log cancellazione prenotazioni."""
    log_user_action(
        utente=instance.utente,
        action_type='booking_cancelled',
        message=f"Prenotazione cancellata: {instance.risorsa.nome}",
        related_booking=instance
    )
