#!/bin/bash
set -e

echo "🚀 AVVIO SISTEMA PRENOTAZIONI SCOLASTICHE"
echo "========================================"
echo "Timestamp: $(date)"
echo "Branch: ${GIT_BRANCH:-unknown}"
echo "Commit: ${GIT_COMMIT:-unknown}"
echo "========================================"

# Funzione per log di deploy
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /tmp/deploy.log
}

# Funzione per cleanup in caso di errore
cleanup() {
    log "❌ ERRORE: Cleanup in corso..."
    exit 1
}

# Setup error handling
trap cleanup ERR

# Step 1: Verifica connessione database
log "⏳ Verifica connessione database..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if python manage.py migrate --check 2>/dev/null; then
        log "✅ Database connesso correttamente"
        break
    fi
    
    attempt=$((attempt + 1))
    log "⏳ Tentativo $attempt/$max_attempts - Attesa database..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    log "❌ ERRORE: Impossibile connettersi al database dopo $max_attempts tentativi"
    exit 1
fi

# Step 2: Verifica e sistema migrazioni
log "🔧 Verifica stato migrazioni..."
python manage.py showmigrations prenotazioni

# Step 3: Applica migrazioni
log "🚀 Applicazione migrazioni..."
python manage.py migrate --settings=config.settings

# Step 4: Verifica integrità database
log "� Verifica integrità database..."
python manage.py check --settings=config.settings

# Step 5: Popola dati iniziali se necessario
log "📊 Creazione dati iniziali..."
python manage.py fix_database

# Step 6: Verifica finale
log "✅ Verifica finale del sistema..."
if python manage.py shell -c "
from prenotazioni.models import Configuration, SchoolInfo, DeviceCategory
configs = Configuration.objects.count()
school = SchoolInfo.objects.count()
categories = DeviceCategory.objects.count()
print(f'✅ Configurazioni: {configs}, Scuole: {school}, Categorie: {categories}')
if configs > 0 and school > 0:
    print('✅ Sistema pronto per l\\'uso!')
else:
    print('⚠️ Alcuni dati potrebbero essere mancanti')
" 2>/dev/null; then
    log "✅ Sistema verificato e funzionante!"
else
    log "⚠️ Verifica incompleta ma continuando..."
fi

# Step 7: Colleziona static files se necessario
log "📁 Preparazione static files..."
python manage.py collectstatic --noinput --settings=config.settings

log "🎉 SETUP COMPLETATO CON SUCCESSO!"
log "========================================"
log "Sistema pronto per l'uso"
log "URL: https://prenotazioni-scuola.onrender.com"
log "========================================"

# Avvia l'applicazione
log "🎯 Avvio applicazione Django..."
exec "$@"
