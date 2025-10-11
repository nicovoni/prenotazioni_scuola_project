#!/usr/bin/env bash
# Simple development launcher (bash)
# Usage: ./scripts/run-dev.sh

set -euo pipefail

echo "Starting development server with DJANGO_DEBUG=True"
export DJANGO_DEBUG=True

# If you have a .env file in backend/, you can source it (uncomment next line):
# set -a; source backend/.env; set +a

cd backend
python manage.py migrate --noinput || true
python manage.py runserver 0.0.0.0:8000
