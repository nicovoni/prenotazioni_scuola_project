import os
from pathlib import Path
import dj_database_url
import logging as _logging

# BASE_DIR e variabili di progetto
BASE_DIR = Path(__file__).resolve().parent.parent

# ===================
# Email configurazione (Brevo/Sendinblue o Gmail)
# ===================
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'n.cantalupo@isufol.it')
ADMINS = [("Admin", ADMIN_EMAIL)]

# Configurazione email principale
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp-relay.brevo.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() in ('1', 'true', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', ADMIN_EMAIL)
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', 15))

# --- Nuovo: supporto secret file (Render mounts) ---
EMAIL_HOST_PASSWORD_FILE = os.environ.get('EMAIL_HOST_PASSWORD_FILE')  # es. /etc/secrets/email_password.txt
if not EMAIL_HOST_PASSWORD and EMAIL_HOST_PASSWORD_FILE:
    try:
        with open(EMAIL_HOST_PASSWORD_FILE, 'r', encoding='utf-8') as f:
            EMAIL_HOST_PASSWORD = f.read().strip()
    except Exception:
        _logging.getLogger('prenotazioni').exception('Failed reading EMAIL_HOST_PASSWORD_FILE: %s', EMAIL_HOST_PASSWORD_FILE)
        EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD or ''

# --- Nuovo: supporto BREVO HTTP API key (fallback) ---
BREVO_API_KEY = os.environ.get('BREVO_API_KEY')
# fallback: if not set, try reading same secret file (common pattern)
if not BREVO_API_KEY and EMAIL_HOST_PASSWORD_FILE:
    try:
        with open(EMAIL_HOST_PASSWORD_FILE, 'r', encoding='utf-8') as f:
            candidate = f.read().strip()
            if candidate:
                BREVO_API_KEY = candidate
    except Exception:
        _logging.getLogger('prenotazioni').exception('Failed reading BREVO API candidate from file: %s', EMAIL_HOST_PASSWORD_FILE)
        BREVO_API_KEY = BREVO_API_KEY or None

EMAIL_SEND_VIA_BREVO_API = bool(BREVO_API_KEY)

EMAIL_CONFIG = {
    'HOST': EMAIL_HOST,
    'PORT': EMAIL_PORT,
    'USER': EMAIL_HOST_USER,
    'PASSWORD': EMAIL_HOST_PASSWORD,
    'USE_TLS': EMAIL_USE_TLS,
    'USE_SSL': EMAIL_USE_SSL,
    'TIMEOUT': EMAIL_TIMEOUT,
    'SEND_VIA_BREVO_API': EMAIL_SEND_VIA_BREVO_API,
    'BREVO_API_KEY': BREVO_API_KEY,
    'EMAIL_HOST_PASSWORD_FILE': EMAIL_HOST_PASSWORD_FILE,
    # Brevo-specific tuning
    'BREVO_TIMEOUT': int(os.environ.get('BREVO_TIMEOUT', os.environ.get('EMAIL_TIMEOUT', EMAIL_TIMEOUT))),
    'BREVO_RETRIES': int(os.environ.get('BREVO_RETRIES', '3')),
}

# Small runtime hints useful in Render logs
_logger = _logging.getLogger('prenotazioni')
if EMAIL_SEND_VIA_BREVO_API:
    _logger.warning('BREVO_API_KEY detected: HTTP API fallback enabled for sending emails.')
elif EMAIL_HOST and 'brevo' in EMAIL_HOST and not EMAIL_HOST_PASSWORD:
    _logger.warning('EMAIL_HOST configured for Brevo but no password found; SMTP may fail on Render free tier.')

# Provide quick hints about Brevo tuning
_logger.info(f"EMAIL timeout={EMAIL_TIMEOUT}, BREVO timeout={EMAIL_CONFIG['BREVO_TIMEOUT']}, BREVO retries={EMAIL_CONFIG['BREVO_RETRIES']}")

# Configurazioni SMTP avanzate per migliorare affidabilità
EMAIL_BACKEND_CONFIG = {
    'timeout': EMAIL_TIMEOUT,
    'fail_silently': False,
}

# Configurazioni specifiche per provider
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

# Use environment variable with secure fallback only for development
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if os.environ.get('DJANGO_DEBUG', 'False') == 'True':
        SECRET_KEY = 'dev-secret-key-change-in-production-12345678901234567890'
    else:
        raise ValueError('DJANGO_SECRET_KEY environment variable is required in production')

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# ALLOWED_HOSTS configuration for Render
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

# Security settings
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
        default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'),
        # Ottimizzazioni per free tier Render
        conn_max_age=600,  # 10 minuti connessione persistente
        conn_health_checks=True,  # Controllo stato connessione
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
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =========================
# Whitenoise static files optimization
# =========================
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# =========================
# Optimized Caching & Performance
# =========================

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

# =========================
# Optimized Logging Configuration
# =========================

# Logging minimale per Render free tier
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'ERROR',
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
            'level': 'ERROR',
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
