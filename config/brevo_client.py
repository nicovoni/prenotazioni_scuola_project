import os
import requests

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

def send_brevo_email(to_email: str, subject: str, html_content: str, sender_email: str, api_key: str = None, timeout: int = 10):
	"""
	Simple Brevo (Sendinblue) SMTP API fallback.
	Raises requests.RequestException on network/API failures.
	"""
	api_key = api_key or os.environ.get("BREVO_API_KEY")
	if not api_key:
		raise RuntimeError("BREVO_API_KEY not configured")

	payload = {
		"sender": {"email": sender_email},
		"to": [{"email": to_email}],
		"subject": subject,
		"htmlContent": html_content
	}
	headers = {
		"api-key": api_key,
		"Content-Type": "application/json"
	}
	resp = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=timeout)
	resp.raise_for_status()
	return resp.json()
