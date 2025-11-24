import os
from celery import Celery

# Imposta il modulo settings di Django come default per Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('prenotazioni_scuola_project')

# Carica la configurazione da Django settings con prefisso CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in installed apps
app.autodiscover_tasks()

# Default broker fallback
from django.conf import settings
if not getattr(settings, 'CELERY_BROKER_URL', None):
    app.conf.broker_url = os.environ.get('CELERY_BROKER_URL', os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
