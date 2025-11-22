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

# Post-migrate: verify critical tables exist and print diagnostics
# Set SKIP_TABLE_CHECK=1 to bypass this verification (useful for some CI or legacy cases)
if [ "${SKIP_TABLE_CHECK:-0}" != "1" ]; then
	echo "Verifying critical database tables..."
	# Default critical tables (space-separated). Override via CRITICAL_TABLES env var.
	CRITICAL_TABLES=${CRITICAL_TABLES:-"prenotazioni_profiloutente prenotazioni_prenotazione prenotazioni_risorsa"}

	python - <<'PY'
import os
import sys
import django
from django.db import connection, ProgrammingError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
	django.setup()
except Exception as e:
	print('ERROR: could not setup Django:', e)
	sys.exit(2)

tables = set(connection.introspection.table_names())
crit = os.environ.get('CRITICAL_TABLES', '').strip() or "prenotazioni_profiloutente prenotazioni_prenotazione prenotazioni_risorsa"
missing = []
for t in crit.split():
	if t not in tables:
		missing.append(t)

print('Existing tables (sample):', ', '.join(sorted(list(tables))[:20]))
if missing:
	print('\nERROR: Missing critical tables:')
	for m in missing:
		print(' -', m)
	# Try to provide more diagnostics where possible
	try:
		from django.db import connection
		with connection.cursor() as cursor:
			print('\nAttempting to list django_migrations entries for prenotazioni...')
			cursor.execute("SELECT app, name, applied FROM django_migrations WHERE app='prenotazioni' ORDER BY applied DESC LIMIT 50;")
			rows = cursor.fetchall()
			if rows:
				for r in rows:
					print('  ', r)
			else:
				print('  No migration records found for app "prenotazioni"')
	except Exception as de:
		print('  Could not query migration records:', de)
	# Fail the entrypoint so the deploy is clearly marked unhealthy
	print('\nDeploy failed: critical DB tables missing. Set SKIP_TABLE_CHECK=1 to bypass this check.')
	sys.exit(3)
else:
	print('All critical tables present.')
PY
fi

# Exec passed command (e.g. gunicorn)
exec "$@"
