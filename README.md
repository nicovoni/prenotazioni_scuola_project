## Deploy su Render

1. Crea un nuovo servizio web su Render usando il Dockerfile.
2. Imposta le variabili ambiente:
	- `DJANGO_SECRET_KEY`
	- `DJANGO_DEBUG`
	- `DJANGO_ALLOWED_HOSTS`
	- `DATABASE_URL` (usa la stringa Supabase: `postgresql://<SUPABASE_USER>:<SUPABASE_PASSWORD>@<SUPABASE_HOST>:5432/<SUPABASE_DB>`)
3. Avvia il servizio: Render eseguirà le migrazioni e avvierà Gunicorn tramite `entrypoint.sh`.

### Configurazione Email con Google Workspace

Per inviare email tramite Google Workspace (es. account n.cantalupo@isufol.it):

1. **Genera una password per le app** su Google:
   - Accedi all'account Google Workspace (es. n.cantalupo@isufol.it)
   - Vai su Account Google > Sicurezza > Verifica in due passaggi (deve essere attiva)
   - Vai su "Password per le app" e genera una nuova password per "Mail" / "Altro dispositivo"
   - Copia la password generata (16 caratteri senza spazi)

2. **Configura il Secret File su Render**:
   - Vai su Dashboard Render > Il tuo servizio > Settings
   - Scorri fino a "Secret Files"
   - Clicca su "Add Secret File"
   - Filename: `email_password.txt` (Render aggiunge automaticamente il percorso /etc/secrets/)
   - Contents: Incolla la password per le app (solo la password, niente altro)
   - Salva (il file sarà disponibile in `/etc/secrets/email_password.txt`)

3. **Imposta le variabili d'ambiente su Render**:
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=n.cantalupo@isufol.it
   EMAIL_HOST_PASSWORD_FILE=/etc/secrets/email_password.txt
   DEFAULT_FROM_EMAIL=n.cantalupo@isufol.it
   ADMIN_EMAIL=n.cantalupo@isufol.it
   ```

4. **Verifica la configurazione**:
   Dopo il deploy, usa la shell di Render o esegui il comando di test:
   ```bash
   python manage.py send_test_pin destinatario@isufol.it
   ```

**Nota importante**: Con Google Workspace, assicurati che:
- L'account mittente (EMAIL_HOST_USER) abbia la verifica in due passaggi attiva
- La password utilizzata sia quella generata dalle "Password per le app", NON la password normale dell'account
- Il dominio del mittente corrisponda al dominio configurato in SCHOOL_EMAIL_DOMAIN (isufol.it)

## Database Supabase

Configura Supabase come database PostgreSQL e copia la stringa di connessione in `DATABASE_URL`.

## Variabili personalizzabili

Vedi `.env.example` per branding, orari, carrelli, preavviso.

### Snippet per Render > Environment

**Opzione 1: Con Google Workspace (usando Secret Files)**

```
DJANGO_SECRET_KEY=supersegreto
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.onrender.com,yourdomain.com
DATABASE_URL=postgresql://<USER>:<PASS>@<HOST>:5432/<DB>
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=n.cantalupo@isufol.it
EMAIL_HOST_PASSWORD_FILE=/etc/secrets/email_password.txt
DEFAULT_FROM_EMAIL=n.cantalupo@isufol.it
ADMIN_EMAIL=n.cantalupo@isufol.it
SCHOOL_EMAIL_DOMAIN=isufol.it
```

**IMPORTANTE**: Quando usi Google Workspace, devi anche configurare il Secret File su Render:
- Settings > Secret Files > Add Secret File
- Filename: `email_password.txt` (inserisci solo il nome, non il percorso completo)
- Contents: La password per le app generata da Google (16 caratteri)
- Render lo posizionerà automaticamente in `/etc/secrets/email_password.txt`

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

Se usi Docker Compose localmente, puoi usare lo script `scripts/run-in-docker.sh` per eseguire il comando di test all'interno del container web.
## Sviluppo e testing

Per evitare errori SMTP in ambiente di sviluppo (che possono causare 500 Internal Server Error quando il server email non è configurato), il progetto usa un fallback: quando `DJANGO_DEBUG` è impostato a `True`, Django utilizzerà il `console.EmailBackend` e mostrerà le email (incluso il PIN) direttamente sulla console del server.

Come attivare il fallback (solo per sviluppo locale):

```bash
# dalla cartella backend
export DJANGO_DEBUG=True
# poi avviare il server Django (es. con manage.py)
python manage.py runserver
```

Questo permette di vedere il contenuto dell'email (il PIN) nella console anziché inviarlo via SMTP.

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
