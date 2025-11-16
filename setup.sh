#!/bin/bash

# ========================================
# Setup Script per Sistema di Prenotazioni Scolastiche
# ========================================

set -e

echo "🚀 Setup del Sistema di Prenotazioni Scolastiche"
echo "================================================"

# Controlla se Python è installato
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trovato. Installa Python 3.8+ prima di continuare."
    exit 1
fi

# Controlla se siamo nella directory giusta
if [ ! -f "requirements.txt" ]; then
    echo "❌ File requirements.txt non trovato. Esegui lo script dalla directory principale del progetto."
    exit 1
fi

echo "📦 Installazione dipendenze Python..."
pip install -r requirements.txt

echo "🔧 Configurazione Django..."

# Crea file .env se non esiste
if [ ! -f ".env" ]; then
    echo "📝 Creazione file .env da .env.example..."
    cp .env.example .env
    echo "⚠️  MODIFICA .env con i tuoi valori reali prima di avviare l'applicazione!"
else
    echo "✅ File .env già esistente"
fi

# Raccogli input per configurazione base
echo ""
echo "⚙️  Configurazione base (premi Enter per valori di default):"

read -p "Nome scuola [Istituto Statale di Istruzione Superiore di Follonica]: " school_name
school_name=${school_name:-"Istituto Statale di Istruzione Superiore di Follonica"}

read -p "Email amministratore [admin@scuola.it]: " admin_email
admin_email=${admin_email:-"admin@scuola.it"}

read -p "Dominio email scuola [scuola.it]: " school_domain
school_domain=${school_domain:-"scuola.it"}

read -p "Usare SQLite per development? (y/n) [y]: " use_sqlite
use_sqlite=${use_sqlite:-"y"}

# Genera secret key Django se non presente
if ! grep -q "DJANGO_SECRET_KEY=your-super-secret-key-here" .env 2>/dev/null; then
    echo "✅ SECRET_KEY già configurata"
else
    secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    sed -i.bak "s/DJANGO_SECRET_KEY=.*/DJANGO_SECRET_KEY=$secret_key/" .env
    echo "🔑 SECRET_KEY generata automaticamente"
fi

# Configurazione database SQLite
if [ "$use_sqlite" = "y" ]; then
    sed -i.bak "s|# DATABASE_URL=sqlite:///db.sqlite3|DATABASE_URL=sqlite:///db.sqlite3|" .env
    sed -i.bak "s|DATABASE_URL=postgresql://.*|DATABASE_URL=sqlite:///db.sqlite3|" .env
    echo "💾 Configurato per usare SQLite (development)"
fi

# Aggiorna configurazione scuola
sed -i.bak "s|^SCHOOL_NAME=.*|SCHOOL_NAME=$school_name|" .env
sed -i.bak "s|^ADMIN_EMAIL=.*|ADMIN_EMAIL=$admin_email|" .env
sed -i.bak "s|^SCHOOL_EMAIL_DOMAIN=.*|SCHOOL_EMAIL_DOMAIN=$school_domain|" .env

# Rimuovi backup
rm -f .env.bak

echo ""
echo "🗄️  Setup database..."

# Migrazioni Django
python manage.py migrate
echo "✅ Migrazioni eseguite"

echo ""
echo "👤 Creazione utente admin..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(is_superuser=True).delete(); User.objects.create_superuser('admin', '$admin_email', '123456')" | python manage.py shell || true

echo ""
echo "📧 Test configurazione email..."
python manage.py sendtestemail admin@$school_domain || echo "⚠️  Configura l'email nel file .env per abilitare gli invii"

echo ""
echo "🎉 Setup completato!"
echo ""
echo "🚀 Avvio server di sviluppo:"
echo "python manage.py runserver"
echo ""
echo "Admin panel: http://localhost:8000/admin"
echo "Username: admin"
echo "Password: 123456"
echo ""
echo "⚠️  CAMBIA SUBITO LA PASSWORD DELL'ADMIN!"
echo ""
echo "📝 Modifica .env per personalizzare ulteriormente la configurazione"
