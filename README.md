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
