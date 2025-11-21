#!/usr/bin/env bash
set -e

echo
echo "Running migrations..."

# Semplificato per Render free tier
echo "Waiting for database to be ready..."
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

# Exec passed command (e.g. gunicorn)
exec "$@"
