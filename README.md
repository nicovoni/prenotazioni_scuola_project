## Deploy su Render

1. Crea un nuovo servizio web su Render usando il Dockerfile.
2. Imposta le variabili ambiente:
	- `DJANGO_SECRET_KEY`
	- `DJANGO_DEBUG`
	- `DJANGO_ALLOWED_HOSTS`
	- `DATABASE_URL` (usa la stringa Supabase: `postgresql://<SUPABASE_USER>:<SUPABASE_PASSWORD>@<SUPABASE_HOST>:5432/<SUPABASE_DB>`)
3. Avvia il servizio: Render eseguirà le migrazioni e avvierà Gunicorn tramite `entrypoint.sh`.

### Configurazione Email con Google/Gmail

Per inviare email tramite Gmail (account nicolacantalup@gmail.com):

1. **Genera una password per le app** su Gmail:
   - Accedi all'account Gmail nicolacantalup@gmail.com
   - Vai su [myaccount.google.com](https://myaccount.google.com) > Sicurezza
   - Attiva la "Verifica in due passaggi" se non già attiva
   - Vai su "Password per le app" > Seleziona app "Mail" e dispositivo "Altro"
   - Copia la password generata (16 caratteri senza spazi)

2. **Configura il Secret File su Render**:
   - Dashboard Render > Il tuo servizio > Settings > Secret Files
   - Clicca "Add Secret File"
   - Filename: `email_password.txt` (Render aggiunge automaticamente `/etc/secrets/`)
   - Contents: Incolla solo la password per le app
   - Salva (disponibile come `/etc/secrets/email_password.txt`)

3. **Imposta le variabili d'ambiente su Render**:
   ```
   EMAIL_HOST=smtp.gmail.com
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

**Importante**: Assicurati che l'account abbia la verifica in due passaggi attiva e usa una "Password per le app", NON la password normale.

## Database Supabase

Configura Supabase come database PostgreSQL e copia la stringa di connessione in `DATABASE_URL`.

## Variabili personalizzabili

Vedi `.env.example` per branding, orari, carrelli, preavviso.

### Snippet per Render > Environment

**Opzione 1: Con Gmail personale (consigliato)**

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

**Opzione 2: Con SendGrid**

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

**Opzione 3: Con Amazon SES (Consigliato - Generoso piano gratuito)**

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
cd c:\Users\giorg\progetti\prenotazioni_scuola_project\backend
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

Esegui il comando di test via docker-compose (se usi docker-compose):

```bash
# esegue il comando send_test_pin all'interno del container web
docker-compose run --rm web python manage.py send_test_pin i.nizzo@isufol.it
```

Deliverability
---------------
Per migliorare la deliverability (evitare che le email finiscano in spam) configura i record DNS del tuo dominio (`isufol.it`) relativi a SPF, DKIM e DMARC. Se non gestisci il dominio, chiedi all'amministratore di sistema o al provider di hosting per assistenza.
