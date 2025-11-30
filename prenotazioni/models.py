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
from django.db.models.signals import post_save, post_delete, post_migrate
from django.dispatch import receiver
import logging

# =====================================================
# SCELTE GLOBALI
# =====================================================

SCELTE_SESSO = [
    ('M', 'Maschio'),
    ('F', 'Femmina'),
    ('ALTRO', 'Altro'),
]


# =============================================================================
# UTENSILI AUSILIARI
# =============================================================================

def genera_codice_univoco():
    """Genera un codice univoco per elementi del sistema."""
    # Return a UUID instance (preferred for UUIDField defaults)
    return uuid.uuid4()


# =============================================================================
# MANAGER PERSONALIZZATI PER SOFT-DELETE
# =============================================================================

class SoftDeleteManager(models.Manager):
    """Manager che filtra automaticamente record soft-deleted."""
    def get_queryset(self):
        return super().get_queryset().filter(cancellato_il__isnull=True)


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet personalizzato per soft-delete."""
    def delete(self):
        """Soft-delete: marca come cancellato invece di rimuovere."""
        return self.update(cancellato_il=timezone.now())
    
    def hard_delete(self):
        """Hard-delete: rimozione fisica dal database."""
        return super().delete()
    
    def deleted(self):
        """Filtra solo record cancellati."""
        return self.filter(cancellato_il__isnull=False)
    
    def all_including_deleted(self):
        """Include anche record soft-deleted."""
        return super().get_queryset()


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
        help_text='Indirizzo completo (compatibile con servizi di geocoding come OpenStreetMap/Nominatim)'
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
    ruolo_utente = models.CharField(
        max_length=30,
        choices=[
            ('admin', 'Amministratore'),
            ('docente', 'Docente'),
            ('studente', 'Studente'),
            ('assistente', 'Assistente'),
            ('altro', 'Altro'),
        ],
        default='studente',
        verbose_name='Ruolo Utente',
        help_text='Ruolo principale dell’utente nel sistema'
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

    # RIMOSSO: i seguenti campi erano duplicati da User + ProfiloUtente
    # - nome_utente (usa User.first_name + ProfiloUtente.nome_battesimo)
    # - cognome_utente (usa User.last_name)
    # - sesso_utente (usa ProfiloUtente.sesso)
    # - data_nascita_utente (usa ProfiloUtente.data_nascita)
    # - codice_fiscale_utente (usa ProfiloUtente.codice_fiscale)
    # - telefono_utente (usa ProfiloUtente.telefono)
    # - email_personale_utente (usa User.email)
    
    @property
    def sessione_scaduta(self):
        # Restituisce True se la sessione è scaduta. Se la data di scadenza
        # non è impostata, consideriamo la sessione NON scaduta.
        if not self.data_scadenza_sessione:
            return False
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
    nome = models.CharField(max_length=100)  # Non unique: molte scuole hanno lo stesso nome
    codice_meccanografico = models.CharField(
        max_length=20,
        unique=True,  # Unique: da scuole_anagrafe.csv
        blank=True,
        verbose_name='Codice Meccanografico',
        help_text='Codice scuola/plesso (CODICESCUOLA dal CSV) - identificatore univoco'
    )
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

    # Localizzazione - CORRETTA: FK a UbicazioneRisorsa (obbligatoria)
    ubicazione = models.ForeignKey(
        UbicazioneRisorsa,
        on_delete=models.PROTECT,
        verbose_name='Ubicazione Dispositivo',
        help_text='Localizzazione fisica del dispositivo'
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
    cancellato_il = models.DateTimeField(null=True, blank=True, help_text='Soft-delete: data di cancellazione')

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

    # Audit - NUOVO: chi ha creato/modificato
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='dispositivi_creati'
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='dispositivi_modificati'
    )

    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)

    # Manager personalizzato per soft-delete
    objects = SoftDeleteManager.as_manager()
    all_objects = models.Manager()  # Per recuperare anche cancellati

    class Meta:
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivi'
        ordering = ['tipo', 'marca', 'nome']
        indexes = [
            models.Index(fields=['codice_inventario']),
            models.Index(fields=['tipo', 'stato']),
            models.Index(fields=['categoria']),
            models.Index(fields=['attivo']),
            models.Index(fields=['ubicazione']),
            models.Index(fields=['cancellato_il']),
        ]

    def clean(self):
        """Validazione coerenza dati dispositivo."""
        if self.codice_inventario and len(self.codice_inventario) < 3:
            from django.core.exceptions import ValidationError
            raise ValidationError({'codice_inventario': 'Il codice inventario deve essere di almeno 3 caratteri.'})
        if self.data_scadenza_garanzia and self.data_acquisto and self.data_scadenza_garanzia < self.data_acquisto:
            from django.core.exceptions import ValidationError
            raise ValidationError({'data_scadenza_garanzia': 'La data di scadenza garanzia non può essere precedente alla data di acquisto.'})

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

    # Localizzazione - CORRETTA: obbligatoria (NOT NULL)
    localizzazione = models.ForeignKey(
        UbicazioneRisorsa,
        on_delete=models.PROTECT,
        verbose_name='Ubicazione Risorsa'
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
    cancellato_il = models.DateTimeField(null=True, blank=True, help_text='Soft-delete: data di cancellazione')

    def clean(self):
        """Validazione coerenza dispositivi associati."""
        if self.is_carrello() or self.is_laboratorio():
            if self.dispositivi.count() == 0:
                from django.core.exceptions import ValidationError
                raise ValidationError({'dispositivi': 'Devi associare almeno un dispositivo a questa risorsa.'})
        if self.capacita_massima is not None and self.capacita_massima < 1:
            from django.core.exceptions import ValidationError
            raise ValidationError({'capacita_massima': 'La capacità massima deve essere almeno 1.'})

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

    # Audit - NUOVO: chi ha creato/modificato
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='risorse_create'
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='risorse_modificate'
    )

    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)

    # Manager personalizzato per soft-delete
    objects = SoftDeleteManager.as_manager()
    all_objects = models.Manager()  # Per recuperare anche cancellate

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
            models.Index(fields=['cancellato_il']),
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
        return self.dispositivi.filter(attivo=True, stato='disponibile', cancellato_il__isnull=True)


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


class PrenotazioneDispositivo(models.Model):
    """
    Tabella intermedia per tracciare dispositivi specifici in prenotazioni.
    
    Cattura:
    - Quale dispositivo specifico è assegnato a quale prenotazione
    - In che quantità
    - Stato di assegnazione (assegnato, in preparazione, restituito)
    - Timestamp di assegnazione e restituzione
    """
    STATO_ASSEGNAZIONE = [
        ('assegnato', 'Assegnato'),
        ('in_preparazione', 'In Preparazione'),
        ('restituito', 'Restituito'),
        ('danneggiato', 'Danneggiato'),
        ('smarrito', 'Smarrito'),
    ]

    prenotazione = models.ForeignKey(
        'Prenotazione',
        on_delete=models.CASCADE,
        related_name='dispositivi_assegnati'
    )
    dispositivo = models.ForeignKey(
        'Dispositivo',
        on_delete=models.PROTECT,  # Non permettere cancellazione dispositivo con assegnazioni
        related_name='assegnazioni_prenotazione'
    )
    
    quantita = models.PositiveIntegerField(default=1)
    stato_assegnazione = models.CharField(
        max_length=20,
        choices=STATO_ASSEGNAZIONE,
        default='assegnato'
    )
    
    data_assegnazione = models.DateTimeField(auto_now_add=True)
    data_restituzione = models.DateTimeField(null=True, blank=True)
    
    # Audit
    note_assegnazione = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Dispositivo Prenotazione'
        verbose_name_plural = 'Dispositivi Prenotazioni'
        unique_together = [['prenotazione', 'dispositivo']]
        indexes = [
            models.Index(fields=['prenotazione', 'stato_assegnazione']),
            models.Index(fields=['dispositivo', 'data_assegnazione']),
        ]
    
    def __str__(self):
        return f"{self.prenotazione.id} - {self.dispositivo.nome} ({self.quantita}x)"


class Prenotazione(models.Model):
    """
    Prenotazione di risorse con workflow avanzato.
    
    NOTA IMPORTANTE: I dispositivi specifici sono ora gestiti tramite PrenotazioneDispositivo
    (intermediate model) che sostituisce il vecchio dispositivi_selezionati M2M.
    Accedi ai dispositivi tramite: prenotazione.dispositivi_assegnati.all()
    """
    PRIORITA = [
        ('bassa', 'Bassa'),
        ('normale', 'Normale'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    STATO_PRENOTAZIONE = [
        ('bozza', 'In Bozza'),
        ('in_attesa_approvazione', 'In Attesa di Approvazione'),
        ('approvata', 'Approvata'),
        ('in_corso', 'In Corso'),
        ('completata', 'Completata'),
        ('annullata', 'Annullata'),
        ('rinviata', 'Rinviata'),
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

    # RIMOSSO: dispositivi_selezionati M2M
    # SOSTITUITO DA: PrenotazioneDispositivo (vedere modello sopra)
    # I dispositivi sono ora accedibili via: prenotazione.dispositivi_assegnati.all()

    # Dettagli prenotazione
    inizio = models.DateTimeField(verbose_name='Inizio')
    fine = models.DateTimeField(verbose_name='Fine')
    numero_persone = models.PositiveIntegerField(default=1)
    quantita = models.PositiveIntegerField(default=1)
    priorita = models.CharField(
        max_length=20,
        choices=PRIORITA,
        default='normale'
    )

    # Stato e workflow - simplificato per coerenza
    stato = models.CharField(
        max_length=30,
        choices=STATO_PRENOTAZIONE,
        default='bozza'
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

    # Audit trail - NUOVO: created_by, modified_by per traccia completa
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='prenotazioni_create'
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='prenotazioni_modificate'
    )

    # Timestamp
    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)
    cancellato_il = models.DateTimeField(null=True, blank=True)

    # Manager con soft-delete
    objects = SoftDeleteManager.as_manager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = 'Prenotazione'
        verbose_name_plural = 'Prenotazioni'
        ordering = ['-inizio']
        # INDICI MIGLIORATI per rilevazione conflitti e query frequenti
        indexes = [
            # Rilevazione conflitti: trova prenotazioni della stessa risorsa in intervallo sovrapposto
            models.Index(fields=['risorsa', 'inizio', 'fine']),
            # Query per prenotazioni dell'utente
            models.Index(fields=['utente', 'inizio']),
            # Filtri di stato
            models.Index(fields=['stato']),
            models.Index(fields=['stato', 'inizio']),
            # Intervalli temporali (per query di disponibilità)
            models.Index(fields=['inizio', 'fine']),
            # Soft-delete
            models.Index(fields=['cancellato_il']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(fine__gt=models.F('inizio')),
                name='prenotazione_fine_dopo_inizio'
            ),
        ]

    def __str__(self):
        return f"{self.utente.username} - {self.risorsa.nome} ({self.inizio.strftime('%d/%m/%Y %H:%M')})"

    def clean(self):
        """Validazione della prenotazione - IMPORTANTE: include capacità e conflitti."""
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        # Controllo base: fine dopo inizio
        if self.fine <= self.inizio:
            raise ValidationError({
                'fine': 'L\'orario di fine deve essere successivo all\'inizio.'
            })
        
        # Validazione capacità
        if self.risorsa.capacita_massima and self.numero_persone > self.risorsa.capacita_massima:
            raise ValidationError({
                'numero_persone': f'Massimo {self.risorsa.capacita_massima} persone per questa risorsa.'
            })
        
        # Controllo anticipo minimo/massimo
        if self.inizio < timezone.now() + timezone.timedelta(days=self.risorsa.prenotazione_anticipo_minimo):
            raise ValidationError({
                'inizio': f'Devi prenotare almeno {self.risorsa.prenotazione_anticipo_minimo} giorni in anticipo.'
            })
        
        if self.inizio > timezone.now() + timezone.timedelta(days=self.risorsa.prenotazione_anticipo_massimo):
            raise ValidationError({
                'inizio': f'Non puoi prenotare più di {self.risorsa.prenotazione_anticipo_massimo} giorni in anticipo.'
            })

    def check_conflitti(self):
        """Verifica se ci sono conflitti di prenotazione con altre risorse."""
        conflitti = Prenotazione.objects.filter(
            risorsa=self.risorsa,
            inizio__lt=self.fine,
            fine__gt=self.inizio,
            stato__in=['approvata', 'in_corso'],
            cancellato_il__isnull=True
        ).exclude(id=self.id if self.id else -1)
        return conflitti.exists()

    def get_dispositivi_assegnati(self):
        """Recupera tutti i dispositivi assegnati a questa prenotazione."""
        return self.dispositivi_assegnati.select_related('dispositivo', 'dispositivo__ubicazione')

    def get_dispositivi_per_ubicazione(self):
        """Raggruppa dispositivi per ubicazione."""
        dispositivi = self.get_dispositivi_assegnati()
        per_ubicazione = {}
        for assegnazione in dispositivi:
            loc = str(assegnazione.dispositivo.ubicazione)
            if loc not in per_ubicazione:
                per_ubicazione[loc] = []
            per_ubicazione[loc].append(assegnazione.dispositivo)
        return per_ubicazione

    def cancel(self, user, reason=""):
        """Cancella la prenotazione (soft-delete)."""
        from django.utils import timezone
        if not self.can_be_cancelled_by(user):
            return False, "Non hai i permessi per cancellare questa prenotazione"

        self.cancellato_il = timezone.now()
        self.stato = 'annullata'

        if reason:
            self.note_amministrative += f"\nCancellata da {user.username}: {reason}"

        self.save()
        return True, "Prenotazione cancellata con successo"

    @property
    def durata_minuti(self):
        if self.inizio and self.fine:
            return int((self.fine - self.inizio).total_seconds() / 60)
        return 0

    @property
    def durata_ore(self):
        minutes = self.durata_minuti
        return round(minutes / 60, 2) if minutes else 0

    @property
    def is_passata(self):
        return self.fine < timezone.now() if self.fine else False

    @property
    def is_futura(self):
        return self.inizio > timezone.now() if self.inizio else False

    @property
    def is_in_corso(self):
        now = timezone.now()
        return (self.inizio <= now <= self.fine) if (self.inizio and self.fine) else False

    def can_be_cancelled_by(self, user):
        """Semplice controllo permessi per cancellare la prenotazione."""
        if user is None:
            return False
        # Admin può sempre cancellare
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return True
        # L'utente che ha creato la prenotazione può cancellarla se non è già cancellata
        if self.utente == user and self.cancellato_il is None:
            return True
        return False

    def can_be_modified_by(self, user):
        """Controllo permessi per modificare la prenotazione."""
        if user is None:
            return False
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return True
        if self.utente == user and (self.inizio is None or self.inizio > timezone.now()) and self.cancellato_il is None:
            return True
        return False

    def approve(self, approvatore):
        """Segna la prenotazione come approvata da un admin/operatore."""
        try:
            self.approvazione_richiesta = True
            self.approvato_da = approvatore
            self.data_approvazione = timezone.now()
            self.stato = 'approvata'
            self.save()
            return True
        except Exception as e:
            import logging
            logging.getLogger('prenotazioni').exception('Errore in approve() for booking %s', getattr(self, 'id', None))
            return False


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
                cognome_utente=getattr(instance, 'last_name', '') or '',
                ruolo_utente='admin' if getattr(instance, 'is_staff', False) else 'studente'
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
            # Log full exception but do not block flow
            logging.getLogger('prenotazioni').exception('Failed to log booking_created signal for booking %s', getattr(instance, 'id', None))

def log_booking_deletion_signal(sender, instance, **kwargs):
    """Log cancellazione prenotazioni."""
    # Passa l'utente come primo argomento al helper `log_user_action`.
    try:
        log_user_action(
            instance.utente,
            'booking_cancelled',
            f"Prenotazione cancellata: {instance.risorsa.nome}",
            related_booking=instance
        )
    except Exception:
        logging.getLogger('prenotazioni').exception('Failed to log booking_cancelled for booking %s', getattr(instance, 'id', None))


# Signals registration helper
def connect_signals():
    """Connect signals when the app is ready.

    This helper is called from `AppConfig.ready()` so we can avoid
    registering signals during management commands like `migrate`.
    """
    try:
        post_save.connect(create_user_profile_signal, sender=User)
    except Exception:
        logging.getLogger('prenotazioni').exception('Failed to connect signals')
