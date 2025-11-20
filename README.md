## Deploy su Render

1. Crea un nuovo servizio web su Render usando il Dockerfile.
2. Imposta le variabili ambiente:
	- `DJANGO_SECRET_KEY`
	- `DJANGO_DEBUG`
	- `DJANGO_ALLOWED_HOSTS`
	- `DATABASE_URL` (usa la stringa Supabase: `postgresql://<SUPABASE_USER>:<SUPABASE_PASSWORD>@<SUPABASE_HOST>:5432/<SUPABASE_DB>`)
3. Avvia il servizio: Render eseguirà le migrazioni e avvierà Gunicorn tramite `entrypoint.sh`.

### Configurazione Email con Brevo (ex Sendinblue)

Per inviare email tramite Brevo (alternativa europea a SES, GDPR-compliant):

1. **Crea un account Brevo**:
   - Vai su [brevo.com](https://www.brevo.com/) e registrati
   - Verifica il tuo indirizzo email
   - Vai su SMTP & API > Chiavi API SMTP
   - Crea una nuova chiave API (Master password)

2. **Configura il Secret File su Render**:
   - Dashboard Render > Il tuo servizio > Settings > Secret Files
   - Clicca "Add Secret File"
   - Filename: `email_password.txt` (Render aggiunge automaticamente `/etc/secrets/`)
   - Contents: Incolla la chiave API Brevo
   - Salva (disponibile come `/etc/secrets/email_password.txt`)

3. **Imposta le variabili d'ambiente su Render**:
   ```
   EMAIL_HOST=smtp-relay.brevo.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=nicolacantalup@gmail.com
   EMAIL_HOST_PASSWORD_FILE=/etc/secrets/email_password.txt
   DEFAULT_FROM_EMAIL=nicolacantalup@gmail.com
   ADMIN_EMAIL=nicolacantalup@gmail.com
   ```

4. **Verifica la configurazione**:
   Dopo deploy, testa con:
   ```bash
   python manage.py send_test_pin i.nizzo@isufol.it
   ```

**Vantaggi di Brevo**:
- Piano gratuito: 300 email/giorno
- Server europei (Francia)
- GDPR-compliant
- Eccellente deliverability
- Dashboard di monitoraggio completo

## Database Supabase

Configura Supabase come database PostgreSQL e copia la stringa di connessione in `DATABASE_URL`.

## Variabili personalizzabili

Vedi `.env.example` per branding, orari, carrelli, preavviso.

### Snippet per Render > Environment

**Opzione 1: Con Brevo (Raccomandato - Europeo, GDPR-compliant)**

```
DJANGO_SECRET_KEY=supersegreto
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.onrender.com,yourdomain.com
DATABASE_URL=postgresql://<USER>:<PASS>@<HOST>:5432/<DB>
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=nicolacantalup@gmail.com
EMAIL_HOST_PASSWORD_FILE=/etc/secrets/email_password.txt
DEFAULT_FROM_EMAIL=nicolacantalup@gmail.com
ADMIN_EMAIL=nicolacantalup@gmail.com
SCHOOL_EMAIL_DOMAIN=isufol.it
```

**IMPORTANTE**: Con Brevo, devi configurare il Secret File:
- Dashboard Render > Servizio > Settings > Secret Files
- Add Secret File: Filename `email_password.txt` → Contents: chiave API Brevo (Master password)

**Opzione 2: Con Gmail personale**

```
DJANGO_SECRET_KEY=supersegreto
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.onrender.com,yourdomain.com
DATABASE_URL=postgresql://<USER>:<PASS>@<HOST>:5432/<DB>
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=nicolacantalup@gmail.com
EMAIL_HOST_PASSWORD_FILE=/etc/secrets/email_password.txt
DEFAULT_FROM_EMAIL=nicolacantalup@gmail.com
ADMIN_EMAIL=nicolacantalup@gmail.com
SCHOOL_EMAIL_DOMAIN=isufol.it
```

**IMPORTANTE**: Con Gmail, devi configurare il Secret File:
- Dashboard Render > Servizio > Settings > Secret Files
- Add Secret File: Filename `email_password.txt` → Contents: password per le app Gmail (16 caratteri)

**Opzione 3: Con SendGrid**

```
DJANGO_SECRET_KEY=supersegreto
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.onrender.com,yourdomain.com
DATABASE_URL=postgresql://<USER>:<PASS>@<HOST>:5432/<DB>
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<SENDGRID_API_KEY>
DEFAULT_FROM_EMAIL=noreply@isufol.it
ADMIN_EMAIL=admin@isufol.it
SCHOOL_EMAIL_DOMAIN=isufol.it
```

**Opzione 4: Con Amazon SES**

```
DJANGO_SECRET_KEY=supersegreto
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.onrender.com,yourdomain.com
DATABASE_URL=postgresql://<USER>:<PASS>@<HOST>:5432/<DB>
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<SES_SMTP_USERNAME>
EMAIL_HOST_PASSWORD=<SES_SMTP_PASSWORD>
DEFAULT_FROM_EMAIL=noreply@isufol.it
ADMIN_EMAIL=admin@isufol.it
SCHOOL_EMAIL_DOMAIN=isufol.it
```

Se usi Docker Compose localmente, puoi usare lo script `scripts/run-in-docker.sh` per eseguire il comando di test all'interno del container web.
## Sviluppo e testing

Eseguire i test locali

Versione consigliata con virtualenv:

```bash
cd c:\Users\giorg\progetti\prenotazioni_scuola_project
python -m venv .venv
source .venv/bin/activate   # su Windows PowerShell usa .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
# oppure con Django test runner:
python manage.py test prenotazioni.tests.test_email_validation
```

Nota: in ambiente di produzione assicurati di impostare `DJANGO_DEBUG=False` e configurare le impostazioni SMTP (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_PASSWORD`, ecc.) tramite variabili d'ambiente.

Mittente email (DEFAULT_FROM_EMAIL)
----------------------------------

Le email (compreso il PIN) sono inviate utilizzando il valore di `DEFAULT_FROM_EMAIL` nel `settings.py`. Per sicurezza e chiarezza:

- Imposta `DEFAULT_FROM_EMAIL` (es. `noreply@isufol.it`) come variabile d'ambiente o nel tuo `.env`.
- Imposta `EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD` per l'autenticazione SMTP; molti provider richiedono che l'account SMTP corrisponda al mittente.

Esempio di variabili d'ambiente per produzione (bash):

```bash
export DJANGO_DEBUG=False
export DEFAULT_FROM_EMAIL='noreply@isufol.it'
export EMAIL_HOST='smtp.tuoserver.it'
export EMAIL_PORT='587'
export EMAIL_USE_TLS='True'
export EMAIL_HOST_USER='noreply@isufol.it'
export EMAIL_HOST_PASSWORD='la_password'
```

Per un workflow di sviluppo efficiente, usa i comandi del Makefile:

```bash
make help      # Mostra tutti i comandi disponibili
make install   # Installa dipendenze
make migrate   # Esegue migrazioni database
make run       # Avvia server di sviluppo
make test      # Esegue test
make clean     # Pulisce file temporanei
```

O esegui direttamente:
```bash
python manage.py test prenotazioni.tests.test_email_validation
```

## 🚀 Ottimizzazioni per Render Free Tier

Questa applicazione è **completamente ottimizzata** per funzionare sul piano gratuito di Render (512MB RAM). Le seguenti ottimizzazioni vengono automaticamente abilitate:

### ⚡ Performance Ottimizzazioni

**Gunicorn Configuration:**
```python
workers = 2
threads = 1
timeout = 30
preload_app = True
max_requests = 1000
```

**Database Connection Pooling:**
```python
conn_max_age=600      # Connessioni persistenti 10 minuti
conn_health_checks=True
```

**Database Query Timeout:** 30 secondi su PostgreSQL

**Memory Management:**
- Cache in-memory abilitata
- Logging ridotto (solo WARNING in produzione)
- Upload limitati a 5MB
- Gzip compression attivo

### 🔧 Come Funziona

Le ottimizzazioni sono automaticamente activate quando `RENDER_FREE_TIER=true` (già configurato).

**Disabilitare ottimizazioni** (per piani superiori):
```bash
export RENDER_FREE_TIER=false
```

**Test locale con limitazioni:**
```bash
RENDER_FREE_TIER=true python manage.py runserver
```

### 📊 Risultati Performance

- **RAM Usage**: Ridotto del 30-40%
- **Startup Time**: Ridotto del 50%
- **Query Response**: Più veloce grazie a connection pooling
- **Background Tasks**: Asincroni con timeout ridotti

Esegui il comando di test via docker-compose (se usi docker-compose):

```bash
# esegue il comando send_test_pin all'interno del container web
docker-compose run --rm web python manage.py send_test_pin i.nizzo@isufol.it
```

Deliverability
---------------
Per migliorare la deliverability (evitare che le email finiscano in spam) configura i record DNS del tuo dominio (`isufol.it`) relativi a SPF, DKIM e DMARC. Se non gestisci il dominio, chiedi all'amministratore di sistema o al provider di hosting per assistenza.

## Note rapide per Render (free tier)

Render free spesso blocca l'egress SMTP (porta 587). Per affidabilità in produzione sul piano gratuito:

- Usare la Brevo HTTP API (porta 443) invece di SMTP quando possibile.
- Impostare la chiave Brevo come Secret File in Render:
  - Filename: `email_password.txt` (viene montato in `/etc/secrets/email_password.txt`)
  - Oppure impostare env var `BREVO_API_KEY`.
- Il progetto contiene uno helper `send_via_brevo.py` che legge `BREVO_API_KEY` (o legge il secret file) e invia le email via HTTPS.
- Per far partire le migrazioni automaticamente, copiare `entrypoint.sh` nell'immagine Docker e impostarlo come ENTRYPOINT:
  - COPY entrypoint.sh /app/entrypoint.sh && chmod +x /app/entrypoint.sh
  - ENTRYPOINT ["/app/entrypoint.sh"]
  - CMD mantiene il comando del server (es. gunicorn)
