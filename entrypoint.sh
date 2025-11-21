#!/usr/bin/env bash
set -e

echo
echo "Running migrations..."

# Semplificato per Render free tier
echo "Running migrations..."
python manage.py migrate --noinput

# Exec passed command (e.g. gunicorn)
exec "$@"
