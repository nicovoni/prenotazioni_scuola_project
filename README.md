## Deploy su Render

1. Crea un nuovo servizio web su Render usando il Dockerfile.
2. Imposta le variabili ambiente:
	- `DJANGO_SECRET_KEY`
	- `DJANGO_DEBUG`
	- `DJANGO_ALLOWED_HOSTS`
	- `DATABASE_URL` (usa la stringa Supabase: `postgresql://<SUPABASE_USER>:<SUPABASE_PASSWORD>@<SUPABASE_HOST>:5432/<SUPABASE_DB>`)
3. Avvia il servizio: Render eseguirà le migrazioni e avvierà Gunicorn tramite `entrypoint.sh`.

## Database Supabase

Configura Supabase come database PostgreSQL e copia la stringa di connessione in `DATABASE_URL`.

## Variabili personalizzabili

Vedi `.env.example` per branding, orari, carrelli, preavviso.

Snippet per incollare in Render > Environment (chiavi = valori d'esempio):

```
DJANGO_SECRET_KEY=supersegreto
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.onrender.com,yourdomain.com
DATABASE_URL=postgresql://<USER>:<PASS>@<HOST>:5432/<DB>
DEFAULT_FROM_EMAIL=noreply@isufol.it
ADMIN_EMAIL=admin@isufol.it
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey   # per SendGrid usare 'apikey' come username
EMAIL_HOST_PASSWORD=<SENDGRID_API_KEY>
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
