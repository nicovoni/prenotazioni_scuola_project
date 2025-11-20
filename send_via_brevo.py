import os
import requests

# Prima prova env var, poi file di secret montato da Render (es. /etc/secrets/email_password.txt)
BREVO_API_KEY = os.environ.get('BREVO_API_KEY')
_secret_file = os.environ.get('EMAIL_HOST_PASSWORD_FILE', '/etc/secrets/email_password.txt')
if not BREVO_API_KEY and os.path.exists(_secret_file):
    try:
        with open(_secret_file, 'r', encoding='utf-8') as f:
            BREVO_API_KEY = f.read().strip()
    except Exception:
        BREVO_API_KEY = None

if not BREVO_API_KEY:
    # Non sollevo eccezione all'import: chi chiama deciderà il fallback
    BREVO_API_KEY = None

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"
DEFAULT_FROM = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')

def send_pin(to_email, subject, html_content, sender_email=None, sender_name="Sistema Prenotazioni"):
    """
    Invia email via Brevo HTTP API. Solleva requests.HTTPError su errore.
    Assicurati di avere BREVO_API_KEY (env o secret file).
    """
    if not BREVO_API_KEY:
        raise RuntimeError("BREVO_API_KEY non impostata. Configura BREVO_API_KEY env var o EMAIL_HOST_PASSWORD_FILE con la chiave.")

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
    }
    sender = {"email": sender_email or DEFAULT_FROM, "name": sender_name}
    payload = {
        "sender": sender,
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    resp = requests.post(BREVO_SEND_URL, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

# Esempio d'uso:
# send_pin("user@example.com", "PIN", "<p>Il tuo PIN: 1234</p>")
