#!/bin/sh
set -e

echo "▶️ Applying database migrations..."
python manage.py makemigrations prenotazioni
python manage.py migrate --noinput

echo "▶️ Checking database initialization..."
# Crea dati iniziali solo se il database è vuoto
python manage.py shell -c "
from prenotazioni.models import Utente, Risorsa
if not Utente.objects.exists() and not Risorsa.objects.exists():
    from django.core.management import call_command
    print('📊 Database vuoto - creando dati iniziali...')
    call_command('create_initial_data')
else:
    risorse_count = Risorsa.objects.count()
    utenti_count = Utente.objects.count()
    print(f'📊 Database già inizializzato - {risorse_count} risorse, {utenti_count} utenti')
"

echo "▶️ Collecting static files..."
python manage.py collectstatic --noinput

echo "▶️ Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT}
