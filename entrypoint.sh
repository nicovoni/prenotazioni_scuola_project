#!/bin/sh
set -e

echo "▶️ Applying database migrations..."
python manage.py makemigrations prenotazioni
python manage.py migrate --noinput

echo "▶️ Creating initial data..."
python manage.py create_initial_data

echo "▶️ Collecting static files..."
python manage.py collectstatic --noinput

echo "▶️ Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT}
