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
        import sys
        import logging
        # Do not connect runtime signals during management commands that operate on the DB schema
        management_cmds = {'makemigrations', 'migrate', 'collectstatic', 'test', 'shell', 'flush'}
        if any(cmd in sys.argv for cmd in management_cmds):
            logging.getLogger('prenotazioni').info('Skipping signal registration during management command: %s', sys.argv)
            return

        try:
            import prenotazioni.models as models  # noqa
            if hasattr(models, 'connect_signals'):
                models.connect_signals()
        except Exception:
            logging.getLogger('prenotazioni').exception('Failed to connect prenotazioni signals')

