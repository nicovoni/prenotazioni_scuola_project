import os
from pathlib import Path
import dj_database_url
import logging as _logging
from datetime import timedelta


# === Percorso base del progetto ===
BASE_DIR = Path(__file__).resolve().parent.parent

###########################################################
# EMAIL: Configurazione SMTP Brevo (o provider compatibile)
###########################################################
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'n.cantalupo@isufol.it')
ADMINS = [("Admin", ADMIN_EMAIL)]


## Configurazione email principale robusta
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp-relay.brevo.com')
try:
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
except Exception:
    EMAIL_PORT = 587
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() in ('1', 'true', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', ADMIN_EMAIL)
try:
    EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', 15))
except Exception:
    EMAIL_TIMEOUT = 15

# Log warning se mancano variabili email essenziali
_logger = _logging.getLogger('prenotazioni')
if not EMAIL_HOST_USER:
    _logger.warning('EMAIL_HOST_USER non impostato: le email potrebbero non essere inviate correttamente.')
if not EMAIL_HOST_PASSWORD and not os.environ.get('EMAIL_HOST_PASSWORD_FILE'):
    _logger.warning('EMAIL_HOST_PASSWORD non impostata: le email potrebbero non essere inviate.')
if not DEFAULT_FROM_EMAIL:
    _logger.warning('DEFAULT_FROM_EMAIL non impostata: usare ADMIN_EMAIL come fallback.')

## Supporto secret file (Render mounts)
EMAIL_HOST_PASSWORD_FILE = os.environ.get('EMAIL_HOST_PASSWORD_FILE')  # es. /etc/secrets/email_password.txt
if not EMAIL_HOST_PASSWORD and EMAIL_HOST_PASSWORD_FILE:
    try:
        with open(EMAIL_HOST_PASSWORD_FILE, 'r', encoding='utf-8') as f:
            EMAIL_HOST_PASSWORD = f.read().strip()
    except Exception:
        _logging.getLogger('prenotazioni').exception('Failed reading EMAIL_HOST_PASSWORD_FILE: %s', EMAIL_HOST_PASSWORD_FILE)
        EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD or ''



# Solo SMTP Brevo: rimosso supporto API HTTP e fallback

## Configurazioni SMTP avanzate per migliorare affidabilità
EMAIL_BACKEND_CONFIG = {
    'timeout': EMAIL_TIMEOUT,
    'fail_silently': False,
}

## Configurazioni specifiche per provider
if EMAIL_HOST == 'smtp-relay.brevo.com':
    # Brevo (Sendinblue) SMTP settings
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    EMAIL_PORT = 587
    # For Brevo, EMAIL_HOST_USER should be your Brevo login (usually your email)
    # EMAIL_HOST_PASSWORD should be your Brevo SMTP key (not API key)

elif EMAIL_HOST == 'smtp.gmail.com':
    # Gmail SMTP settings
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    EMAIL_PORT = 587
    # EMAIL_HOST_USER should be your Gmail address
    # EMAIL_HOST_PASSWORD should be an App Password (not regular password)

###########################################################
# SICUREZZA: Secret key e debug
###########################################################
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if os.environ.get('DJANGO_DEBUG', 'False') == 'True':
        SECRET_KEY = 'dev-secret-key-change-in-production-12345678901234567890'
    else:
        raise ValueError('DJANGO_SECRET_KEY environment variable is required in production')

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# Optional secret key to protect sanity/startup endpoints when DEBUG=False
SANITY_KEY = os.environ.get('SANITY_KEY')

###########################################################
# HOSTS: configurazione allowed hosts
###########################################################
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'web',  # Docker internal
]

# Add Render domain if available
render_external_url = os.environ.get('RENDER_EXTERNAL_URL')
if render_external_url:
    domain = render_external_url.replace('https://', '').replace('http://', '')
    if domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(domain)

# Add any additional hosts from environment
additional_hosts = os.environ.get('ALLOWED_HOSTS')
if additional_hosts:
    for host in additional_hosts.split(','):
        host = host.strip()
        if host and host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)

###########################################################
# APPS: installate
###########################################################
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # REST API
    'rest_framework',
    'corsheaders',

    # App principale
    'prenotazioni',
]

###########################################################
# MIDDLEWARE
###########################################################
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'django.middleware.gzip.GZipMiddleware',  # Disabilitato per risparmio CPU
]

###########################################################
# SICUREZZA: impostazioni avanzate solo in produzione
###########################################################
if not DEBUG:
    # Production security settings
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Cookie security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True

    # Content Security Policy (basic)
    CSP_DEFAULT_SRC = ("'self'",)
    CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
    CSP_SCRIPT_SRC = ("'self'",)
    CSP_IMG_SRC = ("'self'", "data:", "https:")
    CSP_FONT_SRC = ("'self'", "https:")

    # SSL redirection
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = []

###########################################################
# URL e TEMPLATES
###########################################################
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

###########################################################
# DATABASE: configurazione
###########################################################
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'),
        # Ottimizzazioni per free tier Render
        conn_max_age=600,  # 10 minuti connessione persistente
        conn_health_checks=True,  # Controllo stato connessione
    )
}

###########################################################
# PASSWORD: validatori
###########################################################
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

###########################################################
# LOCALIZZAZIONE
###########################################################
LANGUAGE_CODE = 'it-it'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

###########################################################
# STATIC FILES: Whitenoise ottimizzazione
###########################################################
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

###########################################################
# CACHE E PERFORMANCE
###########################################################

# Usa solo LocMemCache per Render free tier
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'booking-system-cache',
    }
}

# Session caching for better performance
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'


###########################################################
# LOGGING: minimale in produzione, dettagliato in debug
###########################################################
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
            },
                'console_debug': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'prenotazioni': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
                'prenotazioni.lookup_unica': {
                    'handlers': ['console_debug'],
                    'level': 'DEBUG',
                    'propagate': False,
                },
        },
    }
else:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
            },
                'console_debug': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                },
        },
        'root': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': False,
            },
            'prenotazioni': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
                'prenotazioni.lookup_unica': {
                    'handlers': ['console_debug'],
                    'level': 'DEBUG',
                    'propagate': False,
                },
        },
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================
# Branding e scuola
# =========================
SCHOOL_NAME = os.environ.get("SCHOOL_NAME", "Istituto Statale di Istruzione Superiore di Follonica")
AUTHOR = os.environ.get("AUTHOR", "Sistema sviluppato da TUO NOME")
SCHOOL_EMAIL_DOMAIN = os.environ.get("SCHOOL_EMAIL_DOMAIN", "isufol.it")

# =========================
# Admin emails
# =========================
ADMINS_EMAIL_LIST = os.environ.get("ADMINS_EMAIL_LIST", "").split(",")
ADMINS_EMAIL_LIST = [email.strip() for email in ADMINS_EMAIL_LIST if email.strip()]

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

# Configurazione login/logout
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Django Sites framework
SITE_ID = 1

# AUTH_USER_MODEL = 'auth.User'  # Default

# =========================
# REST FRAMEWORK Basic Configuration
# =========================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Password policy
PASSWORD_MAX_AGE_DAYS = int(os.environ.get('PASSWORD_MAX_AGE_DAYS', 100))
PASSWORD_HISTORY_COUNT = int(os.environ.get('PASSWORD_HISTORY_COUNT', 5))

# Ensure strong password validators are enabled
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Middleware: insert ForcePasswordChangeMiddleware after AuthenticationMiddleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'prenotazioni.middleware.ForcePasswordChangeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =========================
# DJANGO CORS HEADERS - Basic API Support
# =========================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev
    "http://localhost:8080",  # Vue dev
    "https://your-frontend-domain.com",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB


# Async Celery/Redis rimosso: notifiche solo sincrone o via comando manuale

