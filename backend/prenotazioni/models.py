from django.db import models
from django.contrib.auth.models import AbstractUser

class Utente(AbstractUser):
    # Ruoli disponibili
    RUOLI = [
        ('docente', 'Docente'),
        ('studente', 'Studente'),
        ('assistente', 'Assistente tecnico'),
        ('admin', 'Amministratore'),
    ]
    ruolo = models.CharField(max_length=20, choices=RUOLI, default='studente')
    
    # Campi extra
    telefono = models.CharField(max_length=20, blank=True, null=True)
    classe = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.username


class Risorsa(models.Model):
    TIPO = [
        ('lab', 'Laboratorio'),
        ('carrello', 'Carrello'),
    ]
    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=TIPO)
    quantita_totale = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.nome} ({self.tipo})"


class Prenotazione(models.Model):
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    risorsa = models.ForeignKey(Risorsa, on_delete=models.CASCADE)
    quantita = models.PositiveIntegerField(default=1)
    inizio = models.DateTimeField()
    fine = models.DateTimeField()

    def __str__(self):
        return f"{self.utente} - {self.risorsa} ({self.inizio} → {self.fine})"
