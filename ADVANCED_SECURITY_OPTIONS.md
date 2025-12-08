# 🔐 Configurazioni di Sicurezza Avanzate per AulaMax

Questo documento descrive opzioni di sicurezza avanzate che puoi implementare per proteggerti ulteriormente.

## 1. 2FA (Two-Factor Authentication) per l'Admin

### Implementazione consigliata: TOTP (Time-based One-Time Password)

```bash
# Installare django-otp (One-Time Password)
pip install django-otp qrcode

# Aggiungere a settings.py
INSTALLED_APPS = [
    ...
    'django_otp',
    'django_otp.plugins.otp_totp',
    ...
]

MIDDLEWARE = [
    ...
    'django_otp.middleware.OTPMiddleware',
    ...
]

# Applicare le migrazioni
python manage.py migrate
```

### Uso:

```python
# views_login.py - Dopo l'autenticazione username/password
from django_otp.util import random_hex
from django_otp.plugins.otp_totp.models import StaticDevice, StaticToken

# Controllare se l'utente ha 2FA abilitato
if not user.totpdevice_set.exists():
    # Redirigere al setup 2FA
    return redirect('otp_setup')

# Se ha 2FA, chiedere il token TOTP
# Token è valido per 30 secondi
```

---

## 2. IP Whitelist per l'Admin

Limitare l'accesso al login admin solo da IP conosciuti:

```python
# prenotazioni/middleware.py - NEW

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.conf import settings

class AdminIPWhitelistMiddleware(MiddlewareMixin):
    """
    Permette il login admin solo da IP nella whitelist.
    Configurable via ADMIN_WHITELIST_IPS in settings.
    """
    
    def process_request(self, request):
        # Checkare solo il path /accounts/login/admin/
        if not request.path.startswith('/accounts/login/admin/'):
            return None
        
        # Recuperare IP del client
        client_ip = self.get_client_ip(request)
        
        # Whitelist default: localhost + ALLOWED_HOSTS
        allowed_ips = getattr(settings, 'ADMIN_WHITELIST_IPS', None)
        
        if allowed_ips is None:
            # Nessuna restrizione
            return None
        
        if client_ip not in allowed_ips and '0.0.0.0/0' not in allowed_ips:
            # IP non autorizzato
            return HttpResponseForbidden(
                f'IP {client_ip} non autorizzato per il login admin'
            )
        
        return None
    
    @staticmethod
    def get_client_ip(request):
        """Recuperare l'IP del client, considerando proxy."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Prendere il primo IP nella catena X-Forwarded-For
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

# settings.py
ADMIN_WHITELIST_IPS = [
    '127.0.0.1',           # localhost
    '192.168.1.0/24',      # Rete interna della scuola
    '203.0.113.0/24',      # Rete ospiti (es.)
]
```

---

## 3. Logging e Alerting Avanzato

### Configurare Sentry per monitoraggio real-time:

```bash
pip install sentry-sdk
```

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if not DEBUG:
    sentry_sdk.init(
        dsn="https://your-sentry-key@sentry.io/project-id",
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="production",
    )

# Ora tutti gli errori vengono mandati a Sentry con:
# - Stack trace
# - Browser info
# - IP, User-Agent
# - Custom tags (wizard_step, admin_user_id, etc)
```

### Alert per accessi sospetti:

```python
# prenotazioni/wizard_security.py - EXTEND

def log_wizard_access(request, action, details=None):
    """Esteso con Sentry alerting per azioni critiche."""
    
    # ... codice precedente ...
    
    # Se azione è critica, invia alert
    critical_actions = [
        'wizard_unauthorized_access',
        'wizard_rate_limit_exceeded',
        'wizard_session_mismatch',
    ]
    
    if action in critical_actions:
        import sentry_sdk
        sentry_sdk.capture_message(
            f'SECURITY ALERT: {action}',
            level='warning',
            tags={
                'wizard_action': action,
                'user_id': request.user.id if request.user.is_authenticated else 'anonymous',
                'ip_address': ip_address,
            }
        )
```

---

## 4. Backup Automatico della Configurazione

```python
# prenotazioni/management/commands/backup_config.py - NEW

from django.core.management.base import BaseCommand
from django.utils import timezone
from prenotazioni.models import (
    ConfigurazioneSistema, InformazioniScuola, Risorsa, Dispositivo
)
import json
import os

class Command(BaseCommand):
    help = 'Backup della configurazione di sistema in JSON'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='backup',
            help='Directory di output (default: ./backup)'
        )
    
    def handle(self, *args, **options):
        output_dir = options['output']
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(output_dir, f'config_backup_{timestamp}.json')
        
        backup_data = {
            'timestamp': timezone.now().isoformat(),
            'schema_version': '1.0',
            'configurations': list(
                ConfigurazioneSistema.objects.values()
            ),
            'school_info': list(
                InformazioniScuola.objects.values()
            ),
            'resources': list(
                Risorsa.objects.values()
            ),
            'devices': list(
                Dispositivo.objects.values()
            ),
        }
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Backup salvato: {backup_file}')
        )
```

### Schedulare automaticamente:

```python
# settings.py - Aggiungere celery/scheduled task
# Oppure cron job:

# crontab -e
# 0 2 * * * /path/to/venv/bin/python /path/to/manage.py backup_config

# Questo esegue il backup ogni giorno alle 2:00 AM
```

---

## 5. Session Timeout per Admin

```python
# settings.py

# Session timeout di 8 ore per admin, 30 minuti per altri utenti
SESSION_COOKIE_AGE = 30 * 60  # 30 minuti default

# Middleware per ridurre il timeout all'admin
# prenotazioni/middleware.py - ADD

class AdminSessionTimeoutMiddleware(MiddlewareMixin):
    """Riduce il session timeout per l'admin a 8 ore."""
    
    def process_request(self, request):
        if request.user.is_superuser:
            # Admin: 8 ore
            request.session.set_expiry(8 * 3600)
        else:
            # User normale: 30 minuti
            request.session.set_expiry(30 * 60)
        return None
```

---

## 6. Disable Weak Ciphers in Django

```python
# settings.py - Production only

if not DEBUG:
    # Forzare TLS 1.2+
    SECURE_SSL_REDIRECT = True
    
    # HTTP Strict Transport Security
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Forza HTTPS per tutto
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    
    # Content Security Policy
    CSP_DEFAULT_SRC = ("'self'",)
    CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
    CSP_SCRIPT_SRC = ("'self'",)
    
    # X-Content-Type-Options
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
```

---

## 7. Audit Trail per Tutte le Azioni Admin

```python
# prenotazioni/models.py - ADD

class AuditLog(models.Model):
    """Registro di tutte le azioni dell'admin."""
    
    ACTION_CHOICES = [
        ('create', 'Crea'),
        ('update', 'Modifica'),
        ('delete', 'Elimina'),
        ('configure', 'Configura'),
    ]
    
    admin_user = models.ForeignKey(User, on_delete=models.PROTECT)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)  # Es. 'Risorsa'
    object_id = models.IntegerField(null=True)
    changes = models.JSONField()  # Prima/dopo dei cambiamenti
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['admin_user']),
        ]
    
    def __str__(self):
        return f'{self.admin_user} - {self.action} - {self.model_name} ({self.timestamp})'
```

---

## 8. Rate Limiting Avanzato

### Usare django-ratelimit:

```bash
pip install django-ratelimit
```

```python
# views.py
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='5/15m', method='POST')
def setup_amministratore(request):
    # Max 5 POST requests per user, ogni 15 minuti
    ...
```

---

## 9. LDAP/SSO per Admin (Avanzato)

Se la scuola usa Active Directory o LDAP:

```bash
pip install django-auth-ldap
```

```python
# settings.py
import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

AUTH_LDAP_SERVER_URI = os.environ.get('LDAP_SERVER_URI', '')
AUTH_LDAP_BIND_DN = os.environ.get('LDAP_BIND_DN', '')
AUTH_LDAP_BIND_PASSWORD = os.environ.get('LDAP_BIND_PASSWORD', '')

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "cn=users,dc=example,dc=com",
    ldap.SCOPE_SUBTREE,
    "(uid=%(user)s)"
)

AUTH_LDAP_PROFILE_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',  # Fallback
]
```

---

## 10. Monitoraggio con Prometheus

```bash
pip install django-prometheus
```

```python
# settings.py
INSTALLED_APPS = [
    'django_prometheus',
    ...
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# metrics endpoint: /metrics/
```

Poi usare Grafana per visualizzare:
- Accessi admin per ora/giorno
- Rate limiting triggered count
- Errori di autenticazione
- Tempi di risposta del wizard

---

## Priorità di Implementazione

### 🔴 CRITICO (Implementare prima)
1. Rate limiting (✅ già implementato)
2. Audit logging (✅ già implementato)
3. HTTPS/SSL forzato (già in settings)

### 🟡 IMPORTANTE (Dopo il primo deploy)
1. 2FA per admin
2. IP whitelist
3. Session timeout ridotto

### 🟢 CONSIGLIATO (Lungo termine)
1. Sentry/alerting
2. Backup automatici
3. LDAP/SSO integration

---

## Conclusione

Implementando anche solo le funzioni CRITICHE + IMPORTANTI, l'app sarà significativamente più sicura da attacchi.

La priorità numero uno rimane: **password dell'admin forte + generata in modo sicuro**.

