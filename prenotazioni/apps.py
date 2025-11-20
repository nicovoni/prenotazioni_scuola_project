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
        # Importa i segnali per connetterli automaticamente
        import prenotazioni.models  # noqa
