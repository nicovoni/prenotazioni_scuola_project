import os
from pathlib import Path
import dj_database_url
import structlog
import redis
import sentry_sdk
from datetime import timedelta

# Inizializzazione Sentry per error monitoring
if not DEBUG and os.environ.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[
            sentry_sdk.integrations.django.DjangoIntegration(),
            sentry_sdk.integrations.redis.RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production' if not DEBUG else 'development',
    )

# Configurazione Structlog per logging strutturato avanzato
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.JSONRenderer() if not DEBUG else structlog.dev.ConsoleRenderer(colors=True),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.WriteLoggerFactory(),
    cache_logger_on_first_use=True,
)

# BASE_DIR e variabili di progetto
BASE_DIR = Path(__file__).resolve().parent.parent

# ===================
# Email configurazione (Brevo/Sendinblue o Gmail)
# ===================
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'n.cantalupo@isufol.it')
ADMINS = [("Admin", ADMIN_EMAIL)]

# Configurazione email principale
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp-relay.brevo.com')  # Default Brevo, override with env var
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() in ('1', 'true', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', ADMIN_EMAIL)
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', 15))  # Reduced timeout for faster failure

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



# SMTP password - simplified for Render.com deployment
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Use environment variable with secure fallback only for development
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'dev-secret-key-change-in-production-12345678901234567890'
    else:
        raise ValueError('DJANGO_SECRET_KEY environment variable is required in production')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # REST API e GraphQL
    'rest_framework',
    'graphene_django',
    'corsheaders',

    # Canali e async
    'channels',

    # Performance monitoring
    'silk',
    'cacheops',

    # Sicurezza avanzata
    'csp',
    'django_permissions_policy',

    # App principale
    'prenotazioni',
]

MIDDLEWARE = [
    # Security middleware
    'csp.middleware.CSPMiddleware',
    'django_permissions_policy.PermissionsPolicyMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',

    # Performance monitoring
    'silk.middleware.SilkyMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    # Session and common middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.gzip.GZipMiddleware',
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
# FIXED Logging configuration
# =========================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process} {thread} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'prenotazioni': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# File logging for production
if not os.environ.get('RENDER_FREE_TIER', 'false').lower() == 'true':
    LOGGING['handlers']['file'] = {
        'level': 'WARNING',
        'class': 'logging.FileHandler',
        'filename': os.path.join(BASE_DIR, 'django_errors.log'),
        'formatter': 'verbose',
    }
    LOGGING['handlers']['booking_file'] = {
        'level': 'INFO',
        'class': 'logging.FileHandler',
        'filename': os.path.join(BASE_DIR, 'booking.log'),
        'formatter': 'verbose',
    }
    LOGGING['root']['handlers'].append('file')
    LOGGING['loggers']['prenotazioni']['handlers'].append('booking_file')

# =========================
# Ottimizzazioni per FREE TIER Render (512MB RAM)
# =========================
if os.environ.get('RENDER_FREE_TIER', 'false').lower() == 'true':
    # Logging ridotto per risparmiare memoria
    LOGGING['root']['level'] = 'WARNING'
    LOGGING['root']['handlers'] = ['console']  # Solo console, no file logging
    # Rimuovi file handler se presente
    LOGGING['handlers'].pop('file', None)

    # Cache semplice per ridurre database load
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

    # Limita dimensioni upload per free tier
    FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
    DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB

    # Database query timeout (se supportato dal database)
    DATABASES['default']['OPTIONS'] = {
        'options': '-c statement_timeout=30000'  # 30 secondi timeout
    } if 'postgresql' in DATABASES['default'].get('ENGINE', '') else {}

    # Disabilita Collector automatico per ridurre CPU
    COLLECTOR_DISABLE = True

else:
    # Produzione normale - abilita tutte le features
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
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
# Lista email che hanno accesso come amministratore (vuota di default)
# Gli amministratori vengono creati solo tramite il wizard di configurazione
ADMINS_EMAIL_LIST = os.environ.get("ADMINS_EMAIL_LIST", "").split(",")
# Rimuovi eventuali stringhe vuote dalla lista
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

# =========================
# Altre personalizzazioni
# =========================
# (aggiungi qui altre variabili se necessario)

# Configurazione login/logout
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

AUTH_USER_MODEL = 'prenotazioni.Utente'

# =========================
# CUTTING-EDGE FEATURES - 2025 Modern Web App
# =========================

# =========================
# REDIS Advanced Caching Configuration
# =========================
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Cache Redis avanzato per performance enterprise-level
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
                'decode_responses': True,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'prenotazioni',
        'TIMEOUT': 3600,  # 1 ora default
    },
    'session': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL + '/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'session',
        'TIMEOUT': 86400,  # 24 ore per sessioni
    },
    'template_fragments': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL + '/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'template',
        'TIMEOUT': 1800,  # 30 minuti per template fragments
    }
}

# Session backend Redis per scalabilità
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'

# =========================
# DJANGO CHANNELS - Async WebSockets
# =========================
ASGI_APPLICATION = 'config.asgi.application'

# Channels Redis layer per distribuite deployments
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
            'capacity': 1000,
            'expiry': 30,
        },
    },
}

# =========================
# CELERY - Background Tasks
# =========================
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL + '/3'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Ottimizzazioni Celery per performance
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minuti
CELERY_TASK_TIME_LIMIT = 600       # 10 minuti

# =========================
# CACHEOPS - Smart Database Caching
# =========================
CACHEOPS_REDIS = REDIS_URL + '/4'
CACHEOPS = {
    'prenotazioni.*': {
        'ops': 'get',
        'timeout': 60*15,  # 15 minuti
    },
    'prenotazioni.Booking': {
        'ops': ('get', 'fetch'),
        'timeout': 60*5,   # 5 minuti
    },
    'prenotazioni.Resource': {
        'ops': ('get', 'fetch'),
        'timeout': 60*10,  # 10 minuti
    },
    '*': {
        'timeout': 60*60,  # 1 ora default
    },
}
CACHEOPS_DEGRADE_ON_FAILURE = True
CACHEOPS_LRU = True

# =========================
# GRAPHQL Advanced Configuration
# =========================
GRAPHENE = {
    'SCHEMA': 'prenotazioni.schema.schema',
    'MIDDLEWARE': [
        'graphene_django.debug.DjangoDebugMiddleware',
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
    'SCHEMA_OUTPUT': 'schema.graphql',
    'SCHEMA_INDENT': 2,
}

# GraphQL JWT Authentication
GRAPHQL_JWT = {
    'JWT_PAYLOAD_HANDLER': 'prenotazioni.auth.jwt_payload',
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': timedelta(hours=1),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
    'JWT_SECRET_KEY': SECRET_KEY,
    'JWT_ALGORITHM': 'HS256',
}

# =========================
# REST FRAMEWORK Advanced API
# =========================
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'drf_renderer_xlsx.renderers.XLSXRenderer',  # Export Excel
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'burst': '60/minute',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

# =========================
# DJANGO CORS HEADERS - Modern API Support
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

# =========================
# DJANGO SILK - Performance Profiling
# =========================
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_PYTHON_PROFILER_RESULT_PATH = BASE_DIR / 'profiler_results'
SILKY_MAX_RESPONSE_BODY_SIZE = 1024
SILKY_MAX_REQUEST_BODY_SIZE = 1024
SILKY_META = True
SILKY_INTERCEPT_PERCENT = 50  # Profile 50% of requests

# Silk authorization per admin only
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
SILKY_PERMISSIONS = lambda user: user.is_superuser

# =========================
# PROMETHEUS Metrics
# =========================
PROMETHEUS_METRICS_EXPORT_PORT = 8001
PROMETHEUS_METRICS_EXPORT_ADDRESS = '0.0.0.0'

# =========================
# SECURITY POLICIES ADVANCED
# =========================

# Content Security Policy avanzata
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_SRC = ("'none'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)

# Permissions Policy (ex Feature Policy)
PERMISSIONS_POLICY = {
    "geolocation": [],
    "camera": [],
    "microphone": [],
    "payment": [],
    "usb": [],
    "magnetometer": [],
    "accelerometer": [],
    "gyroscope": [],
    "ambient-light-sensor": [],
    "autoplay": [],
    "encrypted-media": [],
    "fullscreen": [],
    "picture-in-picture": [],
}

# =========================
# ADVANCED SETTINGS
# =========================

# Email asincrono con Celery
CELERY_EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Database ottimizzazioni avanzate
if 'postgresql' in DATABASES['default'].get('ENGINE', ''):
    DATABASES['default']['OPTIONS'].update({
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'charset': 'utf8mb4',
    })

# File upload ottimizzazioni
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB
FILE_UPLOAD_TEMP_DIR = '/tmp' if os.name != 'nt' else None

# Security avanzata
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_EMBEDDER_POLICY = 'require-corp'

# Django 5.1 features
FORMS_URLFIELD_ASSUME_HTTPS = True
CSRF_USE_SESSIONS = False
CSRF_COOKIE_MASKED = True
