import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY','dev-key')
DEBUG = os.environ.get('DEBUG','True') == 'True'
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','rest_framework','prenotazioni']
DATABASES = {'default': {'ENGINE':'django.db.backends.postgresql','NAME': os.environ.get('POSTGRES_DB'),'USER': os.environ.get('POSTGRES_USER'),'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),'HOST': os.environ.get('POSTGRES_HOST'),'PORT': os.environ.get('POSTGRES_PORT')}}
LANGUAGE_CODE='it-it'
TIME_ZONE='Europe/Rome'
STATIC_URL='/static/'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
AUTH_USER_MODEL='prenotazioni.Utente'
SCHOOL_NAME=os.environ.get('SCHOOL_NAME','Scuola')
AUTHOR=os.environ.get('AUTHOR','TUO NOME')
BOOKING_START_HOUR=int(os.environ.get('BOOKING_START_HOUR',8))
BOOKING_END_HOUR=int(os.environ.get('BOOKING_END_HOUR',17))
MIN_NOTICE_DAYS=int(os.environ.get('MIN_NOTICE_DAYS',1))
