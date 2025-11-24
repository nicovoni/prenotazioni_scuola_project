#!/usr/bin/env bash
set -e



# Controllo variabili essenziali
if [ -z "$DJANGO_SECRET_KEY" ]; then
    echo "[WARNING] DJANGO_SECRET_KEY non impostata: usare solo in sviluppo!"
fi
if [ -z "$DATABASE_URL" ]; then
    echo "[WARNING] DATABASE_URL non impostata: verrà usato SQLite locale."
fi
if [ -z "$EMAIL_HOST_USER" ]; then
    echo "[WARNING] EMAIL_HOST_USER non impostata: le email potrebbero non essere inviate."
fi
if [ -z "$EMAIL_HOST_PASSWORD" ] && [ -z "$EMAIL_HOST_PASSWORD_FILE" ]; then
    echo "[WARNING] EMAIL_HOST_PASSWORD e EMAIL_HOST_PASSWORD_FILE non impostate: le email potrebbero non essere inviate."
fi


echo "Running migrations..."
RETRIES=10
until python manage.py migrate --noinput; do
    RETRIES=$((RETRIES-1))
    if [ $RETRIES -le 0 ]; then
        echo "Database not ready after multiple attempts, exiting."
        exit 1
    fi
    echo "Database not ready, retrying in 3 seconds..."
    sleep 3
done

# Check superuser
if ! python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); exit(0) if User.objects.filter(is_superuser=True).exists() else exit(1)"; then
    echo "[WARNING] Nessun superuser trovato: crea un superuser con 'python manage.py createsuperuser'!"
fi

# Avvia il comando richiesto (es. gunicorn)
exec "$@"
