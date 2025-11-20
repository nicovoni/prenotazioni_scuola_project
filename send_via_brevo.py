import os
import requests

BREVO_KEY = os.environ.get("BREVO_API_KEY")
if not BREVO_KEY:
    raise RuntimeError("BREVO_API_KEY non impostata")

def send_pin(to_email, subject, html_content, sender_email=None, sender_name="App"):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_KEY,
        "Content-Type": "application/json",
    }
    sender = {"email": sender_email or os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com"), "name": sender_name}
    payload = {
        "sender": sender,
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

# Esempio d'uso:
# send_pin("user@example.com", "PIN", "<p>Il tuo PIN: 1234</p>")
