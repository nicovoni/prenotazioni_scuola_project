
import os
from pathlib import Path
import dj_database_url

# BASE_DIR e variabili di progetto
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
# Email amministratore unico e configurazione SMTP
# =========================
# Valori predefiniti e lettura sicura da environment variables.
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'noreply@isufol.it')
ADMINS = [("Admin", ADMIN_EMAIL)]

# Backend di default: SMTP. Se in ambiente di sviluppo (DJANGO_DEBUG=True)
# usiamo il console backend per evitare errori quando non è configurato l'SMTP.
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')

# Impostazioni di autenticazione: utilizzare una App Password (consigliato) o un
# secret manager. NON inserire mai la password nel repository.
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', ADMIN_EMAIL)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', ADMIN_EMAIL)

# Development fallback (mostra email in console quando DEBUG=True)
if os.environ.get('DJANGO_DEBUG', 'False').lower() in ('1', 'true'):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Support reading SMTP password from a secret file (e.g. Docker secret)
if not EMAIL_HOST_PASSWORD:
    secret_path = os.environ.get('EMAIL_HOST_PASSWORD_FILE')
    if secret_path and os.path.exists(secret_path):
        try:
            with open(secret_path, 'r', encoding='utf-8') as f:
                EMAIL_HOST_PASSWORD = f.read().strip()
        except Exception:
            # if reading fails, leave EMAIL_HOST_PASSWORD as empty string
            EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'supersegreto123')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'prenotazioni',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(BASE_DIR, 'config', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL')
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'it-it'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# =========================
# Branding e scuola
# =========================
SCHOOL_NAME = os.environ.get("SCHOOL_NAME", "Istituto Comprensivo Roma Nord")
AUTHOR = os.environ.get("AUTHOR", "Sistema sviluppato da TUO NOME")
SCHOOL_EMAIL_DOMAIN = os.environ.get("SCHOOL_EMAIL_DOMAIN", "isufol.it")

# =========================
# Risorse disponibili
# =========================
NUM_LABORATORI = int(os.environ.get("NUM_LABORATORI", 5))
NUM_NOTEBOOK = int(os.environ.get("NUM_NOTEBOOK", 20))
NUM_IPAD = int(os.environ.get("NUM_IPAD", 15))

# =========================
# Configurazione carrelli
# =========================
CART_IPAD_TOTAL = int(os.environ.get("CART_IPAD_TOTAL", 25))
CART_NOTEBOOK_TOTAL = int(os.environ.get("CART_NOTEBOOK_TOTAL", 30))

# =========================
# Regole prenotazione
# =========================
BOOKING_START_HOUR = os.environ.get("BOOKING_START_HOUR", "08:00")
BOOKING_END_HOUR = os.environ.get("BOOKING_END_HOUR", "18:00")
GIORNI_ANTICIPO_PRENOTAZIONE = int(os.environ.get("GIORNI_ANTICIPO_PRENOTAZIONE", 2))
DURATA_MINIMA_PRENOTAZIONE_MINUTI = int(os.environ.get("DURATA_MINIMA_PRENOTAZIONE_MINUTI", 30))
DURATA_MASSIMA_PRENOTAZIONE_MINUTI = int(os.environ.get("DURATA_MASSIMA_PRENOTAZIONE_MINUTI", 180))

# =========================
# Altre personalizzazioni
# =========================
# (aggiungi qui altre variabili se necessario)

AUTH_USER_MODEL = 'prenotazioni.Utente'
