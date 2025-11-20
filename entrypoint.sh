#!/usr/bin/env bash
set -e

: "${DATABASE_HOST:=db}"
: "${DATABASE_PORT:=5432}"
: "${DB_WAIT_TIMEOUT:=60}"
: "${INITIALIZE_DB:=false}"   # impostare su "true" su Render per popolare DB vuoto automaticamente

echo "Waiting for DB at ${DATABASE_HOST}:${DATABASE_PORT} (timeout ${DB_WAIT_TIMEOUT}s)..."
for i in $(seq 1 "${DB_WAIT_TIMEOUT}"); do
  python - <<PY
import socket, os, sys
host = os.environ.get("DATABASE_HOST", "${DATABASE_HOST}")
port = int(os.environ.get("DATABASE_PORT", ${DATABASE_PORT}))
s = socket.socket()
s.settimeout(1)
try:
    s.connect((host, port))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
  if [ $? -eq 0 ]; then
    echo "DB reachable"
    break
  fi
  echo -n "."
  sleep 1
done

echo
echo "Running migrations..."
python manage.py migrate --noinput

if [ "${INITIALIZE_DB}" = "true" ]; then
  echo "INITIALIZE_DB=true -> running initialize_data management command..."
  python manage.py initialize_data || {
    echo "initialize_data failed (non-fatal)"; 
  }
fi

# Optional: collectstatic if you use static files
# python manage.py collectstatic --noinput

# Exec passed command (e.g. gunicorn)
exec "$@"
