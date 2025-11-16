# Guida al Deployment del Sistema di Prenotazioni Scolastiche

Il sistema è progettato per essere altamente portabile e può essere correttamente deployato su qualsiasi servizio cloud o hosting provider.

## 🚀 Deployment Rapido

### Per qualsiasi scuola:
1. **Clona il repository**
2. **Configura le variabili d'ambiente** utilizzando `.env.example`
3. **Scegli il tuo provider** (vedi sezioni specifiche)
4. **Deploy dell'applicazione**

---

## ⚙️ Configurazione Generale

### 1. Variabili d'Ambiente
Copia `.env.example` in `.env` e configura tutti i valori necessari:

```bash
cp .env.example .env
# Modifica .env con i tuoi valori
```

**Variabili obbligatorie:**
- `DJANGO_SECRET_KEY`: Chiave segreta di 50+ caratteri
- `DATABASE_URL`: URL del database (SQLite/PostgreSQL/MySQL)
- `EMAIL_HOST_USER/EMAIL_HOST_PASSWORD`: Credenziali email
- `ADMIN_EMAIL`: Email amministratore principale
- `SCHOOL_NAME`: Nome della scuola

### 2. Database
- **SQLite**: Perfetto per test/development (default)
- **PostgreSQL**: Raccomandato per produzione
- **MySQL**: Supportato ma meno testato

### 3. Email
Supporta tutti i principali provider SMTP:
- **Brevo/Sendinblue** (default)
- **Gmail**
- **Postfix/Sendmail**
- Qualsiasi server SMTP

---

## 🔧 Deployment per Provider

### Railway
```yaml
# railway.toml
[build]
builder = "dockerfile"

[deploy]
healthcheckPath = "/"
```

### Vercel
```json
// vercel.json
{
  "buildCommand": "pip install -r requirements.txt",
  "devCommand": "python backend/manage.py runserver",
  "installCommand": "pip install -r requirements.txt",
  "framework": null
}
```

### Heroku
```yaml
# Procfile
web: gunicorn backend.config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120
```

### DigitalOcean App Platform
```yaml
# .do/app.yaml
name: prenotazioni-scuola
services:
- name: web
  source_dir: /
  github:
    repo: your-username/your-repo
  run_command: gunicorn backend.config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: DATABASE_URL
    type: SECRET
  - key: DJANGO_SECRET_KEY
    type: SECRET
```

### Docker
```bash
# Build dell'immagine
docker build -t prenotazioni-scuola .

# Run locale
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e DJANGO_SECRET_KEY=... \
  prenotazioni-scuola
```

### Docker Compose (development)
```bash
docker-compose up -d
# Accedi su http://localhost:8000
```

### Kubernetes
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prenotazioni-scuola
spec:
  replicas: 2
  selector:
    matchLabels:
      app: prenotazioni-scuola
  template:
    metadata:
      labels:
        app: prenotazioni-scuola
    spec:
      containers:
      - name: prenotazioni-scuola
        image: your-registry/prenotazioni-scuola:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
```

---

## 📋 Checklist Pre-Deployment

- [ ] **Database creato** e accessibile
- [ ] **Email configurata** e testata
- [ ] **DJANGO_SECRET_KEY** generata (50+ caratteri)
- [ ] **DJANGO_ALLOWED_HOSTS** configurato per il dominio
- [ ] **DATABASE_URL** corretta
- [ ] **Migrations eseguite** (`python manage.py migrate`)
- [ ] **Collectstatic eseguito** (`python manage.py collectstatic`)

---

## 🔐 Sicurezza

### 1. Secrets Management
- Non committare mai `.env` nel repository
- Usa i secrets del provider cloud per credenziali sensibili
- Ruota regolarmente le chiavi e password

### 2. HTTPS
- Abilita sempre HTTPS in produzione
- Il sistema supporta automaticamente HTTPS

### 3. Database Security
- Usa connessioni crittografate (SSL)
- Accessi limitati all'IP dell'applicazione
- Ruota regolarmente le credenziali DB

---

## 🐛 Troubleshooting

### Errore 503 Service Unavailable
- Su Render: Free tier si suspende dopo 15 minuti di inattività
- Soluzione: Aumenta a plan paid o usa un cron job per keep-alive

### Email non funziona
```python
# Test email
python manage.py sendtestemail --admin
```

### Database connection failed
- Verifica DATABASE_URL format
- Controlla firewall/accesso al database

### Static files not loading
```bash
python manage.py collectstatic
```

---

## 📞 Supporto

Il sistema è stato progettato per essere autonomo e portabile. Ogni scuola può gestire il proprio deployment e configurazione in completa indipendenza.

Per richieste specifiche di configurazione, aprire una issue nel repository GitHub.
