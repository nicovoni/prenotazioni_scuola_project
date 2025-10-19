# Risoluzione Problemi Email Gmail

## Problema Identificato

Dal log di errore si vede che il sistema va in **WORKER TIMEOUT** durante la connessione SMTP a Gmail. Questo indica che:

1. ✅ La configurazione è corretta (password letta, 16 caratteri)
2. ✅ Le credenziali sono valide
3. ❌ Gmail blocca o limita la connessione dall'IP di Render

## Soluzioni Implementate

### 1. Timeout Aumentato
- Aumentato timeout SMTP da 30 a 60 secondi
- Migliorata gestione errori per evitare crash del worker

### 2. Logging Avanzato
- Log dettagliati per diagnosticare problemi SMTP
- Informazioni configurazione mostrate nel terminale
- Notifiche admin in caso di errori

### 3. Comando Test Email
```bash
cd backend
python manage.py test_email --destinatario tuo@email.it
```

## Possibili Cause del Problema

### 1. Gmail Security Restrictions
Gmail ha restrizioni severe per l'accesso da applicazioni esterne:

**Soluzioni:**
- Assicurati che l'account Gmail abbia attivato "Accesso app meno sicure" (se ancora disponibile)
- Oppure genera una "Password per app" specifica per questo progetto
- Verifica che l'account non abbia 2FA senza password per app configurata

### 2. IP Blocking
L'IP di Render potrebbe essere bloccato da Gmail:

**Soluzioni:**
- Contatta Gmail support per sbloccare l'IP
- Considera l'uso di servizi SMTP alternativi (SendGrid, Mailgun, etc.)

### 3. Rate Limiting
Gmail ha limiti di invio:

**Specifiche:**
- 500 email/giorno per account gratuito
- Limiti per connessioni contemporanee

## Configurazione Alternativa - SendGrid

Per evitare problemi con Gmail, considera l'uso di SendGrid:

### 1. Crea Account SendGrid
1. Vai su [SendGrid](https://sendgrid.com/)
2. Crea account gratuito
3. Verifica email

### 2. Ottieni API Key
1. Vai su Settings > API Keys
2. Crea nuova API Key
3. Salva la chiave

### 3. Configura Environment Variables su Render

Aggiungi queste variabili in Render:

```bash
EMAIL_BACKEND=sendgrid_backend.SendgridBackend
SENDGRID_API_KEY=SG.your_sendgrid_api_key_here
DEFAULT_FROM_EMAIL=your_verified_sender@yourdomain.com
```

### 4. Installa SendGrid
```bash
pip install sendgrid-django
```

## Verifica Configurazione Attuale

### Test Rapido
```bash
cd backend
python manage.py test_email --destinatario tuo@email.it
```

### Debug Output
Il sistema ora mostra:
- Configurazione SMTP completa
- Lunghezza password
- Stato connessione
- Errori dettagliati

## Risoluzione Passo-Passo

### Passo 1: Verifica Password App Gmail
1. Vai su [Google Account Settings](https://myaccount.google.com/)
2. Security > App passwords
3. Genera password per "Mail"
4. Usa questa password nel file `email_password.txt`

### Passo 2: Test Connessione
```bash
python manage.py test_email
```

### Passo 3: Controlla Logs
```bash
tail -f prenotazioni.log
```

### Passo 4: Alternative se Gmail non funziona
1. **SendGrid** (raccomandato) - Più affidabile per produzione
2. **Mailgun** - Alternativa valida
3. **Amazon SES** - Per alti volumi

## Monitoraggio

Il sistema ora:
- ✅ Logga tutti i tentativi di invio email
- ✅ Mostra errori dettagliati per diagnosi
- ✅ Invia notifiche admin in caso di problemi
- ✅ Gestisce i timeout senza crashare il worker

## Supporto

Se il problema persiste, controlla:
1. I log di Render per errori di connessione
2. La configurazione Gmail (2FA, password app)
3. Considera l'uso di servizi SMTP professionali per produzione
