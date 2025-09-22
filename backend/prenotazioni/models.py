from django.db import models
from django.contrib.auth.models import AbstractUser

class Utente(AbstractUser):
    RUOLI=[('docente','Docente'),('studente','Studente'),('assistente','Assistente tecnico'),('admin','Amministratore')]
    ruolo=models.CharField(max_length=20,choices=RUOLI,default='studente')

class Risorsa(models.Model):
    TIPO=[('lab','Laboratorio'),('carrello','Carrello')]
    nome=models.CharField(max_length=120)
    tipo=models.CharField(max_length=20,choices=TIPO)
    quantita_totale=models.PositiveIntegerField(null=True,blank=True)

class Prenotazione(models.Model):
    utente=models.ForeignKey(Utente,on_delete=models.CASCADE)
    risorsa=models.ForeignKey(Risorsa,on_delete=models.CASCADE)
    quantita=models.PositiveIntegerField(default=1)
    inizio=models.DateTimeField()
    fine=models.DateTimeField()
