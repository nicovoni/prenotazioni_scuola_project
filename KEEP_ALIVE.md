# 🏃‍♂️ Keep-Alive per Render Free Tier

**Problema**: Il free tier di Render si suspende dopo 15 minuti di inattività, causando il famoso errore 503 "Service Unavailable".

**Soluzioni**:

## 🔄 Opzione 1: Cron Job Gratuito (Raccomandato)

Usa un servizio gratuito di ping come:
- **UptimeRobot** (50 monitor gratuiti, 5 minuti intervallo)
- **Cron-Job.org** (gratuito fino a 1 ora)
- **Healthchecks.io** (gratuito fino a 20 check)

**Configurazione UptimeRobot**:
```
URL to monitor: https://prenotazioni-scuola.onrender.com/
Monitoring interval: 5 minutes
Monitor type: Ping
```

## 🔧 Opzione 2: GitHub Actions (Free)

Crea un workflow `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Render Alive

on:
  schedule:
    - cron: '*/10 * * * *'  # Ogni 10 minuti

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping app
        run: curl https://prenotazioni-scuola.onrender.com/
```

## ☁️ Opzione 3: Upgrading Render

Passa al piano **Starter** ($7/mese) che ha:
- ✅ No auto-suspend
- ✅ 750 ore gratuite/mese
- ✅ Persistenza database
- ✅ Custom domain gratuito

## 📱 Opzione 4: Monitor Personale

Se vuoi controllare manualmente lo stato:
```bash
# Script semplice per ping
#!/bin/bash
while true; do
  curl -s https://prenotazioni-scuola.onrender.com/ > /dev/null
  echo "Ping $(date)"
  sleep 600  # 10 minuti
done
```

**Nota**: Il primo accesso dopo una sospensione può impiegare 30-60 secondi per riavviarsi completamente.
