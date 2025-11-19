#!/bin/bash
set -e

echo "🚀 AVVIO SISTEMA PRENOTAZIONI SCOLASTICHE"
echo "========================================"

# Attendi che il database sia pronto
echo "⏳ Verifica connessione database..."
python manage.py migrate --check

# Sistema completamente il database
echo "🔧 Sistemazione database completa..."
python manage.py fix_database

# Avvia l'applicazione
echo "🎯 Avvio applicazione Django..."
exec "$@"
