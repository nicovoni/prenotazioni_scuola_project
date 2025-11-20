import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

def send_brevo_email(to_email: str, subject: str, html_content: str, sender_email: str, api_key: str = None, timeout: int = 10):
	"""
	Simple Brevo HTTP fallback. Imports `requests` lazily; if missing, uses urllib.
	Raises exceptions on network/API failures.
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

	# try requests if available (import lazy)
	try:
		import requests  # type: ignore
		resp = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=timeout)
		resp.raise_for_status()
		return resp.json()
	except ModuleNotFoundError:
		# fallback to stdlib urllib
		try:
			data = json.dumps(payload).encode("utf-8")
			req = urllib.request.Request(BREVO_API_URL, data=data, headers=headers, method="POST")
			with urllib.request.urlopen(req, timeout=timeout) as r:
				return json.loads(r.read().decode("utf-8"))
		except urllib.error.HTTPError as he:
			body = he.read().decode("utf-8") if hasattr(he, "read") else ""
			logger.error("Brevo HTTPError %s: %s", he.code, body)
			raise
		except Exception as e:
			logger.error("Brevo urllib fallback failed: %s", e)
			raise
	except Exception as e:
		# re-raise requests exceptions to caller
		logger.error("Brevo requests send failed: %s", e)
		raise
