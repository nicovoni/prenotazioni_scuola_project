# 🔐 Linee Guida di Sicurezza per l'Admin - AulaMax

## 📋 Sommario Esecutivo

La creazione dell'utente amministratore è il **compito più critico** per la sicurezza di AulaMax. Questo documento descrive il processo corretto e sicuro, cosa NON fare, e come monitorare la sicurezza dell'admin.

---

## 1️⃣ Come Creare l'Admin in Sicurezza

### ✅ METODO CORRETTO: `create_admin_securely`

Questo è l'**UNICO** modo sicuro per creare l'admin iniziale:

```bash
# SSH al server
ssh user@tuoserver.com
cd /path/to/aulamax

# Esegui il comando (mostra password una sola volta)
python manage.py create_admin_securely

# Output:
# ======================================================================
# ✅ ADMIN CREATO CON SUCCESSO
# ======================================================================
# 📧 Email: admin@isufol.it
# 👤 Username: admin
# 🔐 Password TEMPORANEA:
#    aB3xY9kM_Qz7wP2nL5vT
# 
# ⚠️  IMPORTANTE:
#    1. COPIA questa password e salvala in password manager
#    2. NON condividerla mai, nemmeno con altri admin
#    3. Al primo login su /accounts/login/admin/, dovrai cambiarla
#    4. La password non può essere recuperata dopo questo messaggio
# ======================================================================
```

### Per un Deploy Automatico (Render, Heroku, etc)

Nel file **Procfile** o **render.yaml**:

```bash
# render.yaml - Esempio per Render
services:
  - type: web
    name: aulamax
    buildCommand: |
      python manage.py migrate
      python manage.py create_admin_securely --email admin@isufol.it --non-interactive
    startCommand: gunicorn config.wsgi
    envVars:
      - key: DJANGO_DEBUG
        value: false
      - key: DJANGO_SECRET_KEY
        value: <use environment variable>
```

### ⚠️ NON FARE MAI:

```python
# ❌ SBAGLIATO: Non usare Django shell per creare admin
python manage.py shell
# >>> from django.contrib.auth import get_user_model
# >>> User = get_user_model()
# >>> User.objects.create_superuser('admin', 'admin@example.com', 'password123')
# ❌ La password è visibile nella shell history!

# ❌ SBAGLIATO: Non mettere password nel codice/variabili d'ambiente
ADMIN_PASSWORD=something  # ❌ NO! La password è in chiaro!

# ❌ SBAGLIATO: Non usare credsentials default o hardcoded
user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')  # ❌

# ❌ SBAGLIATO: Non usare email publicamente conosciute
admin@gmail.com  # ❌ Troppo semplice da indovinare
admin@yourdomain.com  # ❌ Evidente che sia l'admin

# ✅ CORRETTO: Usa email istituzionale + comando sicuro
# admin@isufol.it  # ✅ Email vera della scuola
# python manage.py create_admin_securely  # ✅ Password generata casualmente
```

---

## 2️⃣ Timeline: Quando Creare l'Admin

### 📅 Flow Consigliato:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DEPLOY INIZIALE (t=0)                                    │
│    - Esegui: python manage.py migrate                       │
│    - Esegui: python manage.py create_admin_securely         │
│    - OUTPUT: Password temporanea                            │
│    - SALVA: Password in password manager                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. PRIMO LOGIN ADMIN (t=+5min)                              │
│    - Accedi a: https://yourdomain.com/accounts/login/admin/ │
│    - Username: admin                                        │
│    - Password: [quella generata dal comando]               │
│    - Nota: Wizard richiederà cambio password immediato     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CAMBIO PASSWORD + WIZARD (t=+10min)                      │
│    - Sistema forza cambio password                          │
│    - Configura scuola, dispositivi, risorse                │
│    - Setup wizard completato                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. PRODUCTION (t=+1h)                                       │
│    - Admin attivo con password sicura                       │
│    - Setup completato nel DB                               │
│    - Sistema è operazionale                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3️⃣ Protezioni di Sicurezza Implementate

### 🛡️ Rate Limiting

Il wizard è protetto da attacchi brute-force:

```python
# prenotazioni/wizard_security.py
- Max 5 tentativi di accesso al wizard ogni 15 minuti
- Se superato: accesso bloccato per 15 minuti
- Blocco per IP + user_id (più preciso)
```

**Cosa protegge:**
- Tentativi di indovinare la password durante il wizard
- Accessi malevoli durante il setup
- Attacchi DDoS sul wizard

### 📝 Audit Logging

Ogni accesso sensibile è registrato:

```
wizard_start                 - Admin avvia il wizard
wizard_step_success_school   - Step completato con successo
wizard_step_error_resources  - Step fallito con errore
wizard_completed             - Setup completato
wizard_access_denied         - Accesso negato (non autorizzato)
wizard_rate_limit_exceeded   - Rate limit superato
wizard_session_mismatch      - Tentativo di usare sessione di un altro user
```

**Dove trovare i log:**
```bash
# In Django logs (solitamente in /var/log/aulamax/)
tail -f logs/django.log | grep "WIZARD_EVENT"
tail -f logs/django.log | grep "WIZARD_LOG"
```

### 🔐 Sicurezza della Password Temporanea

```python
# create_admin_securely.py
- Generata con: secrets.token_urlsafe(12)
- Crittograficamente sicura (non sequenziale)
- Lunghezza: ~16 caratteri base64
- Caratteri: [A-Za-z0-9_-]
- Entropia: ~72 bit (resistente a brute force)

Esempio: aB3xY9kM_Qz7wP2nL5vT
         ↑ Maiuscola
               ↑ Numero
                   ↑ Minuscola
                       ↑ Carattere speciale
```

**Resistenza a brute-force:**
```
- Keyspace: ~72 bit
- Tempo per crackare (1 milione di tentativi/sec): ~1000 anni
- Con rate limiting (5 tentativi/15 min): Effettivamente inviolabile
```

---

## 4️⃣ Protezione della Password Permanente

Dopo il cambio password nel wizard, l'admin deve seguire:

### ✅ Buone Pratiche:

1. **Password Manager Obbligatorio**
   ```
   - LastPass, 1Password, Bitwarden, etc.
   - Password >= 16 caratteri
   - Mix: maiuscole, minuscole, numeri, simboli
   - Unica e forte
   ```

2. **Nessuna Condivisione**
   ```
   - Mai condividere con altri admin
   - Mai nel Slack/email
   - Mai nel codice/repository
   - Se condivisa, cambiarla immediatamente
   ```

3. **2FA (Autenticazione Multi-Fattore)**
   ```
   - Se disponibile, abilitare TOTP/Google Authenticator
   - Codice nel password manager
   - Backup codes salvati in luogo sicuro
   ```

4. **Monitoraggio**
   ```
   - Controllare log per accessi insoliti
   - Alert se login da IP diversa
   - Sessioni con timeout (max 8 ore)
   ```

---

## 5️⃣ Scenario: Password Compromessa

### 🚨 Se la password temporanea è scoperta:

1. **Immediato:** Non usarla per il primo login, usa un altra
2. **Reset:** `python manage.py changepassword admin`
3. **Audit:** Controlla i log per accessi non autorizzati
4. **Report:** Documenta l'accaduto nel log di sistema

### 🚨 Se la password permanente è scoperta:

1. **Immediato:** Cambiare password da Django admin
2. **Sessioni:** Invalidare tutte le sessioni dell'admin
3. **Audit:** Rivedere tutte le azioni recenti (ConfigurazioneSistema log)
4. **Review:** Controllare se qualcosa è stato modificato
5. **Reset:** Se necessario, reset completo della configurazione

**Comando di reset password via Django:**
```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(username='admin')
>>> user.set_password('newpassword123')
>>> user.save()
>>> exit()
```

---

## 6️⃣ Monitoraggio Continuo

### 🔍 Log Importanti da Monitorare:

```bash
# 1. Accessi al wizard
grep "WIZARD_EVENT" logs/django.log

# 2. Errori di autenticazione
grep "wizard_unauthorized_access\|wizard_session_mismatch" logs/django.log

# 3. Rate limit exceeded
grep "wizard_rate_limit_exceeded" logs/django.log

# 4. Step completati
grep "wizard_step_success\|wizard_step_error" logs/django.log
```

### 📊 Dashboard di Monitoraggio (da implementare):

Un'idea per il futuro: creare una view admin per visualizzare:
- Ultimi login admin
- Accessi al wizard (con IP)
- Cambimenti di configurazione
- Errori di sicurezza

---

## 7️⃣ Checklist di Sicurezza

### 🔧 Pre-Deploy:

- [ ] Django `SECRET_KEY` impostato in `.env` (non nel codice)
- [ ] `DEBUG = False` in produzione
- [ ] Database usa credenziali sicure (variabili d'ambiente)
- [ ] Email admin configurata correttamente
- [ ] ALLOWED_HOSTS configurato con il dominio corretto
- [ ] HTTPS/SSL forzato in produzione

### 🚀 Deploy Iniziale:

- [ ] Eseguire `python manage.py migrate`
- [ ] Eseguire `python manage.py create_admin_securely`
- [ ] Salvare password temporanea in password manager
- [ ] **NON** pushare password su GitHub/repository
- [ ] Verificare che il log inizi correttamente

### 👤 Primo Login Admin:

- [ ] Accedere a `/accounts/login/admin/`
- [ ] Usare le credenziali generate dal comando
- [ ] Completare il wizard di configurazione
- [ ] Cambiare password a una sicura e personale
- [ ] Salvare la nuova password in password manager

### 📝 Post-Setup:

- [ ] Verificare che `SETUP_COMPLETED` sia nel DB
- [ ] Controllare che il setup flag persista
- [ ] Monitorare i log per attività insolite
- [ ] Configurare alert per accessi non autorizzati
- [ ] Fare backup della configurazione

---

## 8️⃣ Struttura dei File Modificati

```
prenotazioni/
├── wizard_security.py              (NEW)
│   └── Rate limiting + logging
├── management/commands/
│   └── create_admin_securely.py    (NEW)
│       └── Comando di creazione admin
└── views.py                         (MODIFIED)
    └── Aggiunto logging + rate limiting al wizard

config/
└── settings.py                      (REVIEW)
    └── Assicurati che CACHING sia configurato
        └── Per il rate limiting: usa default cache
```

---

## 9️⃣ Variabili d'Ambiente Richieste

```bash
# .env file (NON pushare su Git!)

# Essenziali
DJANGO_SECRET_KEY=<random 50 char string>
DJANGO_DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Email
ADMIN_EMAIL=admin@isufol.it
EMAIL_HOST_USER=your-brevo-email
EMAIL_HOST_PASSWORD=<brevo SMTP password>

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# (Opzionali)
SANITY_KEY=<random key for sanity endpoint>
```

---

## 🔟 FAQ - Domande Frequenti

### D: Posso usare la password temporanea per più di 30 giorni?
**R:** No. Cambiarla dopo il primo login (il wizard forza il cambio). Se non lo fai, changepassword manualmente.

### D: Posso recuperare la password temporanea se la perdo?
**R:** No. È visualizzata solo una volta dal comando. Se persa, reset con:
```bash
python manage.py changepassword admin
```

### D: Posso creare un altro admin con il primo comando?
**R:** No. `create_admin_securely` funziona solo se non esiste un superuser. Se hai bisogno di un secondo admin, usare Django admin.

### D: Cosa succede se il rate limit mi blocca dal wizard?
**R:** Aspetta 15 minuti per il reset automatico. Se urgente, contatta dev per fare flush della cache:
```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### D: Posso disabilitare il rate limiting?
**R:** No. È una protezione essenziale. Ma puoi configurare i limiti in `wizard_security.py`.

### D: Come monitoro chi accede al wizard?
**R:** Controlla i log:
```bash
grep "WIZARD_EVENT\|WIZARD_LOG" logs/django.log
```
O crea una view admin per i log di sistema.

---

## 🔒 Conclusioni

**La sicurezza dell'admin è la fondazione di tutta l'app.**

Seguendo queste linee guida:
- ✅ Password generata in modo crittografico
- ✅ Impossibile indovinare o brute-force
- ✅ Rate limiting contro attacchi
- ✅ Logging completo di ogni accesso
- ✅ Monitoraggio e audit trail
- ✅ Best practices industria

**Ricorda:** Una password debole in una app ben protetta = debolezza. Una password forte in una app mal protetta = debolezza. Entrambe devono essere forti.

---

## 📞 Contatti per Problemi di Sicurezza

Se scopri una vulnerabilità o hai domande sulla sicurezza:
1. **Non** postare pubblicamente su GitHub Issues
2. Contatta il team di sviluppo privatamente
3. Descrivi il problema e l'impatto
4. Fornisci step per riprodurre (se possibile)

