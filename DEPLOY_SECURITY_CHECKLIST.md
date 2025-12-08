# 🚀 Deploy Sicuro di AulaMax - Checklist Rapida

## Step 1: Preparazione Pre-Deploy

```bash
# 1. Verificare che tutte le variabili d'ambiente siano impostate
# Controllare il file .env (NON pushare su GitHub)
cat .env | grep -E "SECRET_KEY|DEBUG|DATABASE"

# 2. Assicurarsi che le migrazioni siano aggiornate
python manage.py migrate --plan

# 3. Testare in locale
python manage.py test
```

## Step 2: Deploy su Server/Render

### Su Render.com

Nel file `render.yaml`:

```yaml
services:
  - type: web
    name: aulamax
    runtime: python-3.11
    buildCommand: |
      python manage.py migrate
      python manage.py create_admin_securely \
        --email admin@isufol.it \
        --non-interactive
    startCommand: gunicorn config.wsgi
    envVars:
      - key: DJANGO_DEBUG
        scope: run
        value: "false"
      - key: DJANGO_SECRET_KEY
        scope: run
        value: ${DJANGO_SECRET_KEY}
      - key: DATABASE_URL
        scope: run
        value: ${DATABASE_URL}
      # ... altre variabili
    healthCheckPath: /health
    healthCheckInterval: 600
    healthCheckTimeout: 60
```

### Su Server Tradizionale

```bash
# SSH al server
ssh user@server.com

# Clonare il repo
git clone https://github.com/nicovoni/aulamax.git
cd aulamax

# Setup virtenv
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure: venv\Scripts\activate  (Windows)

# Installare dipendenze
pip install -r requirements.txt

# Migrazioni
python manage.py migrate

# IMPORTANTE: Creare admin PRIMA di avviare il server
python manage.py create_admin_securely
# ↑ Seguire le istruzioni, salvare la password

# Avviare il server
gunicorn config.wsgi
```

## Step 3: Primo Login Admin

```
1. Aprire il browser: https://yourdomain.com/accounts/login/admin/
2. Username: [quello generato dal comando create_admin_securely]
3. Password: [quella temporanea generata dal comando]
4. IMPORTANTE: Verrà forzato il cambio password
5. Completare il wizard di configurazione
6. Al termine, salvare la nuova password in password manager
```

## Step 4: Verifica Post-Deploy

```bash
# Controllare i log
tail -f logs/django.log

# Verificare che SETUP_COMPLETED sia nel DB
python manage.py shell
>>> from prenotazioni.models import ConfigurazioneSistema
>>> ConfigurazioneSistema.objects.filter(chiave_configurazione='SETUP_COMPLETED').exists()
True  # ← Deve essere True

# Health check
curl https://yourdomain.com/health
# Output: OK

# Sanity check
curl "https://yourdomain.com/api/sanity/?key=YOUR_SANITY_KEY"
```

## Step 5: Monitoraggio Continuo

```bash
# Controllare accessi al wizard
grep "WIZARD_EVENT\|WIZARD_LOG" logs/django.log

# Alert per errori di sicurezza
grep "unauthorized_access\|rate_limit_exceeded\|session_mismatch" logs/django.log

# Controllare login admin
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(username='admin')
>>> user.last_login  # ← Quando è stato l'ultimo accesso
```

## Troubleshooting

### "Admin creato ma login fallisce"

```bash
# Controllare che l'utente esista
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(is_superuser=True).exists()
True  # ← Deve essere True

# Resettare password se necessario
>>> user = User.objects.get(username='admin')
>>> user.set_password('newpassword123')
>>> user.save()
>>> exit()
```

### "Rate limit mi ha bloccato dal wizard"

```bash
# Aspettare 15 minuti, oppure:
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
>>> exit()
```

### "Setup wizard non appare dopo login"

```bash
# Verificare che setup_flag non sia già impostato
python manage.py shell
>>> from prenotazioni.models import ConfigurazioneSistema
>>> ConfigurazioneSistema.objects.all()
# Se SETUP_COMPLETED esiste, il wizard non appare più
# Usa Django admin per modificare la configurazione
```

## 📋 Checklist Finale

- [ ] Variabili d'ambiente configurate
- [ ] Database migrazioni applicate
- [ ] Admin creato con `create_admin_securely`
- [ ] Password temporanea salvata in password manager
- [ ] Primo login completato
- [ ] Password cambiata al nuovo valore
- [ ] Wizard di configurazione completato
- [ ] Setup flag presente nel DB (SETUP_COMPLETED)
- [ ] Health check risponde OK
- [ ] Log monitorati per errori
- [ ] Backup della configurazione eseguito

---

**RICORDA:** Una volta che il setup è completato, il wizard non è più accessibile. Per modificare la configurazione, usa Django admin.

