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
    nome_scuola = models.CharField(
        max_length=200,
        verbose_name='Nome della scuola',
        help_text='Nome completo della scuola'
    )
    indirizzo = models.TextField(
        blank=True,
        null=True,
        verbose_name='Indirizzo',
        help_text='Indirizzo completo della scuola'
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Telefono',
        help_text='Numero di telefono della scuola'
    )
    email_scuola = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email della scuola',
        help_text='Indirizzo email principale della scuola'
    )
    sito_web = models.URLField(
        blank=True,
        null=True,
        verbose_name='Sito web',
        help_text='URL del sito web della scuola'
    )
    codice_scuola = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Codice scuola',
        help_text='Codice identificativo della scuola (es. codice meccanografico)'
    )

    class Meta:
        verbose_name = 'Informazioni scuola'
        verbose_name_plural = 'Informazioni scuola'

    def __str__(self):
        """Rappresentazione stringa delle informazioni scuola."""
        return self.nome_scuola

    @classmethod
    def get_instance(cls):
        """Ottiene l'unica istanza oppure ne crea una vuota se non esiste."""
        instance, created = cls.objects.get_or_create(id=1)
        return instance


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

    # Campi extra
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Telefono',
        help_text='Numero di telefono dell\'utente'
    )
    classe = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Classe',
        help_text='Classe di appartenenza (per studenti)'
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

    Può essere un laboratorio o un carrello di dispositivi.
    """
    TIPO_SCELTE = [
        ('lab', 'Laboratorio'),
        ('carrello', 'Carrello'),
    ]

    nome = models.CharField(
        max_length=120,
        verbose_name='Nome risorsa',
        help_text='Nome identificativo della risorsa'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_SCELTE,
        verbose_name='Tipo',
        help_text='Tipo di risorsa (laboratorio o carrello)'
    )
    quantita_totale = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Quantità totale',
        help_text='Numero totale di postazioni/dispositivi disponibili'
    )

    class Meta:
        verbose_name = 'Risorsa'
        verbose_name_plural = 'Risorse'

    def __str__(self):
        """Rappresentazione stringa della risorsa."""
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
        disponibile = (self.quantita_totale or 1) - quantita_occupata

        return max(0, disponibile), quantita_occupata


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

    class Meta:
        verbose_name = 'Prenotazione'
        verbose_name_plural = 'Prenotazioni'
        ordering = ['-inizio']

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
