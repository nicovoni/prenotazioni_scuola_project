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
        import os
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

        # Schedule delayed startup checks to avoid accessing the DB during app
        # initialization (which raises RuntimeWarning). The checks run in a
        # daemon thread a few seconds after process start.
        try:
            import threading
            import time

            def _delayed_checks():
                try:
                    time.sleep(3)
                    from django.conf import settings
                    from django.db import connection
                    from django.contrib.auth import get_user_model
                    logger = logging.getLogger('prenotazioni.startup')

                    msg = f"prenotazioni delayed startup checks. DEBUG={getattr(settings, 'DEBUG', False)}, SANITY_KEY_SET={bool(getattr(settings, 'SANITY_KEY', None))}"
                    logger.info(msg)
                    try:
                        # Print to stdout as well so platform logs (Render) capture it
                        print(msg, flush=True)
                    except Exception:
                        pass

                    # Try a light DB connectivity check
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute('SELECT 1')
                            cursor.fetchone()
                        logger.info('Database connectivity: OK')
                        try:
                            print('Database connectivity: OK', flush=True)
                        except Exception:
                            pass
                    except Exception as db_e:
                        logger.exception('Database connectivity check failed: %s', db_e)
                        try:
                            print('Database connectivity check failed: %s' % (db_e,), flush=True)
                        except Exception:
                            pass

                    # Read basic counts (non-destructive)
                    try:
                        User = get_user_model()
                        su_count = User.objects.filter(is_superuser=True).count()
                        from .models import Dispositivo
                        dev_count = Dispositivo.objects.count()
                        counts_msg = f'Counts - superusers={su_count}, dispositivi={dev_count}'
                        logger.info(counts_msg)
                        try:
                            print(counts_msg, flush=True)
                        except Exception:
                            pass
                    except Exception as read_e:
                        logger.exception('Error fetching basic counts: %s', read_e)
                        try:
                            print('Error fetching basic counts: %s' % (read_e,), flush=True)
                        except Exception:
                            pass

                except Exception:
                    logging.getLogger('prenotazioni.startup').exception('Unexpected error during delayed startup checks')

            thread = threading.Thread(target=_delayed_checks, daemon=True)
            thread.start()
        except Exception:
            logging.getLogger('prenotazioni.startup').exception('Failed to start delayed startup checks')

