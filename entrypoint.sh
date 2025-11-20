#!/usr/bin/env bash
set -e

: "${DATABASE_HOST:=db}"
: "${DATABASE_PORT:=5432}"
: "${DB_WAIT_TIMEOUT:=60}"

echo "Waiting for DB at ${DATABASE_HOST}:${DATABASE_PORT} (timeout ${DB_WAIT_TIMEOUT}s)..."
for i in $(seq 1 "${DB_WAIT_TIMEOUT}"); do
  python - <<PY
import socket, os, sys
host = os.environ.get("DATABASE_HOST", "db")
port = int(os.environ.get("DATABASE_PORT", 5432))
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

# Run migrations (non-interactive)
echo "Running migrations..."
python manage.py migrate --noinput

# Optional: collectstatic if needed
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Exec the container CMD
exec "$@"
