"""
Modelli per il sistema di prenotazioni scolastiche.

Definisce le entità principali: Utente, Risorsa e Prenotazione.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth import get_user_model


class SchoolInfo(models.Model):
    """
    Informazioni sulla scuola.

    Singola istanza (singleton) per configurazione generale.
    """
    nome = models.CharField(
        max_length=200,
        verbose_name='Nome completo scuola',
        help_text='Nome completo e formale della scuola'
    )
    codice_meccanografico = models.CharField(
        max_length=10,
        verbose_name='Codice meccanografico',
        help_text='Codice meccanografico di identificazione della scuola'
    )
    sito_web = models.URLField(
        verbose_name='URL sito web',
        help_text='URL completo del sito web della scuola'
    )
    indirizzo = models.TextField(
        verbose_name='Indirizzo completo',
        help_text='Indirizzo completo della scuola secondo lo standard di Google Maps'
    )

    class Meta:
        verbose_name = 'Informazioni scuola'
        verbose_name_plural = 'Informazioni scuola'

    def __str__(self):
        """Rappresentazione stringa delle informazioni scuola."""
        return self.nome

    @classmethod
    def get_instance(cls):
        """Ottiene l'unica istanza oppure ne crea una vuota se non esiste."""
        instance, created = cls.objects.get_or_create(id=1)
        return instance


class Device(models.Model):
    """
    Dispositivo disponibile nel sistema scolastico.

    Catalogo di dispositivi che possono essere contenuti nei carrelli.
    Permette di specificare esattamente che tipo di dispositivi sono disponibili.
    """
    # Tipologie base dispositivo
    TIPO_DISPOSITIVO_CHOICES = [
        ('notebook', 'Notebook/Portatile'),
        ('tablet', 'Tablet'),
        ('chromebook', 'Chromebook'),
        ('altro', 'Altro'),
    ]



    nome = models.CharField(
        max_length=100,
        verbose_name='Nome dispositivo',
        help_text='Nome commerciale completo (es. "iPad Pro 12.9" o "Dell Latitude 5420")'
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_DISPOSITIVO_CHOICES,
        verbose_name='Tipo dispositivo',
        help_text='Categoria generale del dispositivo'
    )

    produttore = models.CharField(
        max_length=100,
        verbose_name='Produttore',
        help_text='Azienda produttrice del dispositivo'
    )

    modello = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Modello',
        help_text='Modello specifico del dispositivo'
    )

    attivo = models.BooleanField(
        default=True,
        verbose_name='Attivo',
        help_text='Dispositivo disponibile per l\'uso nei carrelli'
    )

    class Meta:
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivi'
        ordering = ['produttore', 'nome']
        unique_together = ['nome', 'modello']  # Evita duplicati identici

    def __str__(self):
        """Rappresentazione stringa del dispositivo."""
        return f"{self.produttore} {self.nome}"

    def get_display_completo(self):
        """Restituisce una descrizione completa formattata."""
        parts = [self.__str__()]
        if self.modello:
            parts.append(f"({self.modello})")
        return " ".join(parts)

    @property
    def categoria_display(self):
        """Restituisce categoria formattata."""
        return dict(self.TIPO_DISPOSITIVO_CHOICES).get(self.tipo, self.tipo)


class Utente(AbstractUser):
    """
    Utente esteso del sistema di autenticazione Django.

    Include ruoli specifici per il contesto scolastico e campi aggiuntivi.
    """
    # Ruoli disponibili
    RUOLI = [
        ('docente', 'Docente'),
        ('studente', 'Studente'),
        ('assistente', 'Assistente tecnico'),
        ('admin', 'Amministratore'),
    ]

    ruolo = models.CharField(
        max_length=20,
        choices=RUOLI,
        default='studente',
        verbose_name='Ruolo',
        help_text='Ruolo dell\'utente nel sistema scolastico'
    )

    class Meta:
        verbose_name = 'Utente'
        verbose_name_plural = 'Utenti'

    def __str__(self):
        """Rappresentazione stringa dell'utente."""
        return self.username

    def is_docente(self):
        """Verifica se l'utente è un docente."""
        return self.ruolo == 'docente'

    def is_studente(self):
        """Verifica se l'utente è uno studente."""
        return self.ruolo == 'studente'

    def is_assistente(self):
        """Verifica se l'utente è un assistente tecnico."""
        return self.ruolo == 'assistente'

    def is_admin(self):
        """Verifica se l'utente è un amministratore."""
        return self.ruolo == 'admin'



class Risorsa(models.Model):
    """
    Risorsa prenotabile del sistema scolastico.

    Può essere un laboratorio (prenotazione esclusiva) o un carrello (prenotazione condivisa).
    """
    TIPO_SCELTE = [
        ('lab', 'Laboratorio'),
        ('carrello', 'Carrello'),
    ]

    nome = models.CharField(
        max_length=100,
        verbose_name='Nome risorsa',
        help_text='Nome identificativo della risorsa'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_SCELTE,
        verbose_name='Tipo',
        help_text='Tipo di risorsa (laboratorio o carrello)'
    )
    capacita_massima = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Capacità massima',
        help_text='Per carrelli: numero massimo di dispositivi prenotabili contemporaneamente'
    )
    descrizione = models.TextField(
        blank=True,
        verbose_name='Descrizione',
        help_text='Informazioni aggiuntive sulla risorsa (opzionale, max 500 caratteri)'
    )
    dispositivi = models.ManyToManyField(
        Device,
        blank=True,
        related_name='risorse',
        verbose_name='Dispositivi disponibili',
        help_text='Per carrelli: seleziona i tipi di dispositivi disponibili nel carrello'
    )
    attiva = models.BooleanField(
        default=True,
        verbose_name='Attiva',
        help_text='Risorsa disponibile per prenotazioni'
    )

    class Meta:
        verbose_name = 'Risorsa'
        verbose_name_plural = 'Risorse'
        ordering = ['tipo', 'nome']
        indexes = [
            models.Index(fields=['tipo', 'attiva']),  # Query ottimizzate per risorse attive per tipo
            models.Index(fields=['nome']),  # Ricerca per nome
        ]

    def __str__(self):
        """Rappresentazione stringa della risorsa."""
        if self.tipo == 'carrello' and self.capacita_massima:
            dispositivi_info = self.get_dispositivi_display()
            return f"{self.nome} ({self.tipo} - {self.capacita_massima} dispositivi: {dispositivi_info})"
        return f"{self.nome} ({self.tipo})"

    def is_laboratorio(self):
        """Verifica se la risorsa è un laboratorio."""
        return self.tipo == 'lab'

    def is_carrello(self):
        """Verifica se la risorsa è un carrello."""
        return self.tipo == 'carrello'

    def get_disponibilita_in_periodo(self, inizio, fine):
        """
        Calcola la disponibilità della risorsa in un periodo specifico.

        Args:
            inizio: Data/ora inizio periodo
            fine: Data/ora fine periodo

        Returns:
            tuple: (disponibile, quantita_occupata)
        """
        from django.db.models import Sum

        # Query prenotazioni sovrapposte
        overlapping = self.prenotazione_set.filter(
            inizio__lt=fine,
            fine__gt=inizio
        )
        quantita_occupata = overlapping.aggregate(Sum('quantita'))['quantita__sum'] or 0
        disponibile = (self.capacita_massima or 1) - quantita_occupata

        return max(0, disponibile), quantita_occupata

    def get_prenotazioni_in_periodo(self, inizio, fine):
        """
        Restituisce prenotazioni attive in un periodo specifico.

        Args:
            inizio: Data/ora inizio periodo
            fine: Data/ora fine periodo

        Returns:
            QuerySet di Prenotazioni sovrapposte
        """
        return self.prenotazione_set.filter(
            inizio__lt=fine,
            fine__gt=inizio
        ).select_related('utente')

    def get_dispositivi_display(self):
        """Restituisce una stringa con i nomi dei dispositivi disponibili."""
        if self.dispositivi.exists():
            dispositivi_nomi = [d.get_display_completo() for d in self.dispositivi.filter(attivo=True)]
            return ", ".join(dispositivi_nomi)
        return "Nessun dispositivo specificato"

    def get_dispositivi_riassunto(self):
        """Restituisce un riassunto dei tipi di dispositivi disponibili."""
        if self.dispositivi.exists():
            dispositivi_attivi = self.dispositivi.filter(attivo=True)
            tipi = dispositivi_attivi.values_list('tipo', flat=True).distinct()
            tipi_display = [dict(Device.TIPO_DISPOSITIVO_CHOICES).get(tipo, tipo) for tipo in tipi]
            return f"{len(dispositivi_attivi)} dispositivi ({', '.join(tipi_display)})"
        return "Nessun dispositivo disponibile"


class Prenotazione(models.Model):
    """
    Prenotazione di una risorsa da parte di un utente.

    Rappresenta l'associazione tra utente e risorsa per un periodo specifico.
    """
    utente = models.ForeignKey(
        Utente,
        on_delete=models.CASCADE,
        verbose_name='Utente',
        help_text='Utente che ha effettuato la prenotazione'
    )
    risorsa = models.ForeignKey(
        Risorsa,
        on_delete=models.CASCADE,
        verbose_name='Risorsa',
        help_text='Risorsa prenotata'
    )
    quantita = models.PositiveIntegerField(
        default=1,
        verbose_name='Quantità',
        help_text='Numero di postazioni/dispositivi richiesti'
    )
    inizio = models.DateTimeField(
        verbose_name='Data/ora inizio',
        help_text='Inizio del periodo di prenotazione'
    )
    fine = models.DateTimeField(
        verbose_name='Data/ora fine',
        help_text='Fine del periodo di prenotazione'
    )
    attiva = models.BooleanField(
        default=True,
        verbose_name='Attiva',
        help_text='Prenotazione attiva (può essere disabilitata da admin)'
    )
    creato_il = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creato il'
    )
    modificato_il = models.DateTimeField(
        auto_now=True,
        verbose_name='Modificato il'
    )

    class Meta:
        verbose_name = 'Prenotazione'
        verbose_name_plural = 'Prenotazioni'
        ordering = ['-inizio']
        indexes = [
            models.Index(fields=['inizio', 'fine']),  # Range queries per sovrapposizioni
            models.Index(fields=['risorsa', 'inizio', 'fine']),  # Disponibilità per risorsa
            models.Index(fields=['utente', '-inizio']),  # Mie prenotazioni recenti
            models.Index(fields=['attiva']),  # Solo prenotazioni attive
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(fine__gt=models.F('inizio')),
                name='prenotazione_fine_dopo_inizio'
            ),
        ]

    def __str__(self):
        """Rappresentazione stringa della prenotazione."""
        return f"{self.utente} - {self.risorsa} ({self.inizio} → {self.fine})"

    def durata_minuti(self):
        """Calcola la durata della prenotazione in minuti."""
        return int((self.fine - self.inizio).total_seconds() // 60)

    def durata_ore(self):
        """Calcola la durata della prenotazione in ore."""
        return round((self.fine - self.inizio).total_seconds() / 3600, 2)

    def is_passata(self):
        """Verifica se la prenotazione è nel passato."""
        return self.fine < timezone.now()

    def is_futura(self):
        """Verifica se la prenotazione è nel futuro."""
        return self.inizio > timezone.now()

    def is_in_corso(self):
        """Verifica se la prenotazione è attualmente in corso."""
        now = timezone.now()
        return self.inizio <= now <= self.fine

    def sovrappone_con(self, altra_prenotazione):
        """
        Verifica se questa prenotazione sovrappone con un'altra.

        Args:
            altra_prenotazione: Altra istanza di Prenotazione

        Returns:
            bool: True se le prenotazioni si sovrappongono
        """
        return (self.inizio < altra_prenotazione.fine and
                self.fine > altra_prenotazione.inizio)

    def clean(self):
        """Validazione personalizzata del modello."""
        from django.core.exceptions import ValidationError

        if self.fine <= self.inizio:
            raise ValidationError("La data/ora di fine deve essere successiva all'inizio.")

        if self.quantita <= 0:
            raise ValidationError("La quantità deve essere positiva.")

        # Controllo che non ci siano prenotazioni sovrapposte per la stessa risorsa
        # (escludendo se stessa in caso di modifica)
        overlapping = Prenotazione.objects.filter(
            risorsa=self.risorsa,
            inizio__lt=self.fine,
            fine__gt=self.inizio
        )

        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError("Esistono già prenotazioni sovrapposte per questa risorsa.")
