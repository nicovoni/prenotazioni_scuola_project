# 🛡️ Sicurezza Admin AulaMax: Raccomandazioni Complete

## Sommario

Questo documento raccoglie tutte le raccomandazioni, best practice, checklist e opzioni avanzate per la sicurezza dell’utente amministratore di AulaMax. Segui queste linee guida per garantire la massima protezione.

---

## 1️⃣ Sintesi e Flusso Sicuro

- Crea l’admin solo con `python manage.py create_admin_securely`
- Salva la password temporanea in un password manager
- Al primo login, cambia la password con una personale e forte
- Completa il wizard di setup (non ripetibile)
- Il login admin è protetto da rate limiting (5 tentativi/15 min)
- Tutti gli accessi e tentativi sono loggati

---

## 2️⃣ Checklist Pre-Deploy e Deploy

### Pre-Deploy
- [ ] Python 3.11+ e Django 4.2+
- [ ] SECRET_KEY in .env, non nel codice
- [ ] DEBUG = False in produzione
- [ ] ALLOWED_HOSTS configurato
- [ ] HTTPS/SSL attivo
- [ ] Database e email configurati

### Deploy
- [ ] Esegui `python manage.py migrate`
- [ ] Crea admin con `python manage.py create_admin_securely`
- [ ] Salva la password temporanea
- [ ] Avvia il server (es. gunicorn)

### Post-Deploy
- [ ] Primo login admin su `/accounts/login/admin/`
- [ ] Cambia password al primo accesso
- [ ] Completa il wizard
- [ ] Verifica che il flag SETUP_COMPLETED sia nel DB
- [ ] Controlla i log per anomalie

---

## 3️⃣ Password: Cosa Fare e NON Fare

**Corretto:**
- Generata dal comando, mai hardcoded
- Salvata in password manager
- Cambiata subito al primo login
- Mai condivisa

**Sbagliato:**
- Password semplice o di default
- In chiaro nel codice o variabili d’ambiente
- Condivisa via email/Slack

---

## 4️⃣ Protezioni Attive

- Password generata casualmente (72 bit di entropia)
- Rate limiting (5 tentativi/15 min, per IP + user)
- Audit logging (ogni accesso registrato)
- Session validation (admin_user_id in sessione)
- Setup flag (wizard non ripetibile)

---

## 5️⃣ Cosa Fare se Bloccato

**Rate limit superato:**
- Aspetta 15 minuti oppure
- `python manage.py shell` → `from django.core.cache import cache; cache.clear()`

**Password persa:**
- `python manage.py changepassword admin`

**Wizard non appare:**
- Controlla flag SETUP_COMPLETED nel DB

---

## 6️⃣ Monitoraggio e Logging

- Controlla i log: `grep "WIZARD_EVENT" logs/django.log`
- Alert se troppi tentativi falliti o session mismatch
- Backup regolare della configurazione

---

## 7️⃣ Opzioni Avanzate (Consigliate)

- 2FA per admin (django-otp)
- IP whitelist per login admin
- Sentry per alerting avanzato
- Backup automatico della configurazione
- Session timeout ridotto per admin
- Audit trail dettagliato
- Rate limiting avanzato (django-ratelimit)
- LDAP/SSO per ambienti enterprise
- Monitoraggio con Prometheus/Grafana

---

## 8️⃣ FAQ e Troubleshooting

- La password temporanea è mostrata una sola volta: se persa, resettare
- Il wizard non è ripetibile dopo il setup (flag nel DB)
- Rate limiting è essenziale: non disabilitare in produzione
- Per ogni dubbio, contatta lo sviluppatore privatamente

---

## 9️⃣ Conclusione

Seguendo queste raccomandazioni, l’admin di AulaMax è protetto da brute force, session hijacking, password deboli e accessi non autorizzati. La sicurezza è multilivello: anche se una protezione viene aggirata, le altre continuano a difendere il sistema.

**Buon deploy sicuro! 🚀**
