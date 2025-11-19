#!/bin/bash
set -e

# Optimized entrypoint - minimal, fast startup for production deployment
echo "🔧 Starting Django application..."

# Database migration (runs silently, optimized migration handles all tables)
echo "📊 Running database migrations..."
python manage.py shell --settings=config.settings -c "from django.db import connection; with connection.cursor() as c: c.execute(\"DELETE FROM django_migrations WHERE app = 'prenotazioni' AND name = '0001_initial'\"); print('Deleted prenotazioni migration record')"
python manage.py migrate --fake auth --settings=config.settings
python manage.py migrate --fake prenotazioni --settings=config.settings
python manage.py migrate --noinput --settings=config.settings

# Create initial data if needed
echo "📋 Creating initial data..."
python manage.py fix_database --verbosity=0

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --settings=config.settings

# Quick health check (fast validation)
echo "🏥 Running health check..."
python manage.py check --deploy --settings=config.settings

echo "✅ Application ready!"

# Start the application (Gunicorn with optimized settings)
exec "$@"
