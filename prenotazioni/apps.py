from django.apps import AppConfig


class PrenotazioniConfig(AppConfig):
    """
    Configurazione dell'app prenotazioni per il sistema scolastico.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'prenotazioni'
    verbose_name = 'Sistema Prenotazioni Scolastiche'

    def ready(self):
        """
        Codice eseguito quando l'app è pronta.
        """
        import prenotazioni.models  # noqa
        from prenotazioni.models import ProfiloUtente
        ProfiloUtente.objects.filter(nome_utente__isnull=True).update(nome_utente="")
        ProfiloUtente.objects.filter(cognome_utente__isnull=True).update(cognome_utente="")
