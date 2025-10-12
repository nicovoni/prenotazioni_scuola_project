# Configurazione Email Google Workspace su Render

Questo documento descrive i passaggi per configurare l'invio di email tramite Google Workspace (account n.cantalupo@isufol.it) su Render.

## 📋 Prerequisiti

- Account Google Workspace: **n.cantalupo@isufol.it**
- Password per le app Google già generata
- Secret File già configurato su Render nella sezione "Secret Files"

## ✅ Stato Attuale

1. **✓ Password per le app Google**: Generata e salvata come Secret File su Render
2. **✓ Codice applicazione**: Già configurato per leggere la password da file segreto
3. **✓ Documentazione**: README.md aggiornato con le istruzioni

## 🔧 Configurazione su Render

### 1. Secret File (GIÀ FATTO)

Hai già configurato il Secret File su Render:
- **Filename su Render**: `email_password.txt` (Render aggiunge automaticamente `/etc/secrets/`)
- **Percorso finale**: `/etc/secrets/email_password.txt`
- **Contenuto**: Password per le app Google (16 caratteri)
- **Posizione su Render**: Dashboard > Servizio > Settings > Secret Files

### 2. Variabili d'Ambiente da Configurare

Vai su **Dashboard Render > Il tuo servizio > Environment** e assicurati di avere queste variabili:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=n.cantalupo@isufol.it
EMAIL_HOST_PASSWORD_FILE=/etc/secrets/email_password.txt
DEFAULT_FROM_EMAIL=n.cantalupo@isufol.it
ADMIN_EMAIL=n.cantalupo@isufol.it
SCHOOL_EMAIL_DOMAIN=isufol.it
```

**Note importanti**:
- `EMAIL_HOST_PASSWORD_FILE` punta al file segreto che hai già configurato
- NON serve configurare `EMAIL_HOST_PASSWORD` come variabile d'ambiente (il codice legge dal file)
- `EMAIL_HOST_USER` deve essere l'account Google completo

### 3. Come Funziona

Il file `backend/config/settings.py` contiene il seguente codice:

```python
# Support reading SMTP password from a secret file (e.g. Docker secret)
if not EMAIL_HOST_PASSWORD:
    secret_path = os.environ.get('EMAIL_HOST_PASSWORD_FILE')
    if secret_path and os.path.exists(secret_path):
        try:
            with open(secret_path, 'r', encoding='utf-8') as f:
                EMAIL_HOST_PASSWORD = f.read().strip()
        except Exception:
            EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
```

Questo codice:
1. Controlla se esiste la variabile `EMAIL_HOST_PASSWORD_FILE`
2. Legge il contenuto del file segreto
3. Usa la password per configurare l'SMTP

## 🧪 Test della Configurazione

Dopo il deploy, testa l'invio email con:

### Via Shell di Render

1. Vai su Dashboard > Il tuo servizio > Shell
2. Esegui:
```bash
python manage.py send_test_pin i.nizzo@isufol.it
```

### Risultato Atteso

Se tutto funziona correttamente, vedrai:
```
PIN inviato correttamente a i.nizzo@isufol.it. PIN: 123456
```

Se ci sono errori, vedrai un messaggio di errore dettagliato.

## 🔐 Sicurezza

**Vantaggi dell'uso di Secret Files**:
- ✓ La password non è visibile nelle variabili d'ambiente
- ✓ Maggiore sicurezza rispetto a variabili d'ambiente standard
- ✓ Render gestisce i file in modo sicuro (`/etc/secrets/`)

**Cosa NON fare**:
- ❌ Non inserire la password normale dell'account Google
- ❌ Non committare password nel repository Git
- ❌ Non condividere la password per le app

## 🚨 Troubleshooting

### Errore: "Authentication failed"

**Causa**: Password per le app non valida o account senza verifica in due passaggi

**Soluzione**:
1. Verifica che l'account n.cantalupo@isufol.it abbia la verifica in due passaggi attiva
2. Rigenera una nuova password per le app
3. Aggiorna il Secret File su Render con la nuova password
4. Fai un nuovo deploy

### Errore: "File not found"

**Causa**: Il percorso del Secret File non è corretto

**Soluzione**:
1. Verifica che su Render il filename sia esattamente: `email_password.txt` (senza il percorso /etc/secrets/)
2. Render posizionerà automaticamente il file in `/etc/secrets/email_password.txt`
3. Controlla che `EMAIL_HOST_PASSWORD_FILE` punti a `/etc/secrets/email_password.txt`
4. Fai un nuovo deploy

### Errore: "SMTPSenderRefused"

**Causa**: Il mittente non è autorizzato

**Soluzione**:
1. Verifica che `EMAIL_HOST_USER` sia `n.cantalupo@isufol.it`
2. Verifica che `DEFAULT_FROM_EMAIL` sia lo stesso indirizzo
3. Controlla che l'account abbia i permessi per inviare email

## 📧 Funzionamento del Sistema di Autenticazione PIN

Quando un docente richiede l'accesso:

1. **Richiesta email**: Il docente inserisce la sua email (es. `i.nizzo@isufol.it`)
2. **Validazione**: Il sistema verifica che sia del dominio `@isufol.it`
3. **Generazione PIN**: Viene generato un PIN a 6 cifre
4. **Invio email**: Il sistema invia l'email con il PIN tramite `n.cantalupo@isufol.it`
5. **Verifica**: Il docente inserisce il PIN e accede al sistema

## 📚 File Rilevanti

- **Settings**: `backend/config/settings.py` (configurazione SMTP)
- **Invio PIN**: `backend/config/views_email_login.py` (logica di invio)
- **Test**: `backend/prenotazioni/management/commands/send_test_pin.py` (comando di test)
- **Documentazione**: `README.md` (istruzioni generali)

## ✨ Prossimi Passi

1. **Verifica le variabili d'ambiente** su Render (vedi sezione 2)
2. **Fai un deploy** (se hai modificato le variabili)
3. **Testa l'invio** con il comando `send_test_pin`
4. **Prova il login** dall'interfaccia web

---

**Data creazione**: 10/12/2025
**Account email**: n.cantalupo@isufol.it
**Provider**: Google Workspace
**Dominio**: isufol.it
