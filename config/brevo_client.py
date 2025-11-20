import os
import json
import logging
import time
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_brevo_email(
	to_email: str,
	subject: str,
	html_content: str,
	sender_email: str,
	api_key: str = None,
	timeout: int = None,
	retries: int = None,
	backoff_factor: float = 0.5,
):
	"""
	Brevo HTTP send with simple retry/backoff.

	- Tries `requests` if available; otherwise falls back to `urllib`.
	- Retries on transient errors (network issues, 5xx, 429) up to `retries`.
	- Raises on permanent failures.
	"""
	api_key = api_key or os.environ.get("BREVO_API_KEY")
	if not api_key:
		raise RuntimeError("BREVO_API_KEY not configured")

	# defaults from environment if not passed
	try:
		env_timeout = int(os.environ.get("BREVO_TIMEOUT", "10"))
	except Exception:
		env_timeout = 10
	timeout = timeout or env_timeout

	try:
		env_retries = int(os.environ.get("BREVO_RETRIES", "3"))
	except Exception:
		env_retries = 3
	retries = retries if retries is not None else env_retries

	payload = {
		"sender": {"email": sender_email},
		"to": [{"email": to_email}],
		"subject": subject,
		"htmlContent": html_content,
	}
	headers = {
		"api-key": api_key,
		"Content-Type": "application/json",
		"accept": "application/json",
	}

	# Try using requests if available
	try:
		import requests  # type: ignore

		for attempt in range(1, retries + 1):
			try:
				resp = requests.post(
					BREVO_API_URL, json=payload, headers=headers, timeout=timeout
				)
				# Retry on 429 or 5xx
				if resp.status_code >= 500 or resp.status_code == 429:
					msg = f"Brevo transient status {resp.status_code}: {resp.text}"
					logger.warning(msg)
					if attempt == retries:
						resp.raise_for_status()
					else:
						sleep_for = backoff_factor * (2 ** (attempt - 1))
						time.sleep(sleep_for)
						continue
				resp.raise_for_status()
				# return parsed JSON when available
				try:
					return resp.json()
				except ValueError:
					return {"status_code": resp.status_code, "text": resp.text}
			except requests.RequestException as exc:
				logger.warning("Brevo request exception (attempt %s/%s): %s", attempt, retries, exc)
				if attempt == retries:
					logger.error("Brevo send failed after %s attempts", retries)
					raise
				time.sleep(backoff_factor * (2 ** (attempt - 1)))

	except ModuleNotFoundError:
		# Fallback to urllib with simple retry/backoff
		data = json.dumps(payload).encode("utf-8")
		req = urllib.request.Request(BREVO_API_URL, data=data, headers=headers, method="POST")
		last_exc = None
		for attempt in range(1, retries + 1):
			try:
				with urllib.request.urlopen(req, timeout=timeout) as r:
					return json.loads(r.read().decode("utf-8"))
			except urllib.error.HTTPError as he:
				body = he.read().decode("utf-8") if hasattr(he, "read") else ""
				code = getattr(he, 'code', None)
				logger.warning("Brevo HTTPError %s (attempt %s/%s): %s", code, attempt, retries, body)
				last_exc = he
				if code and (code >= 500 or code == 429) and attempt < retries:
					time.sleep(backoff_factor * (2 ** (attempt - 1)))
					continue
				raise
			except Exception as e:
				logger.warning("Brevo urllib exception (attempt %s/%s): %s", attempt, retries, e)
				last_exc = e
				if attempt < retries:
					time.sleep(backoff_factor * (2 ** (attempt - 1)))
					continue
				raise

	except Exception as e:
		# re-raise requests exceptions to caller after logging
		logger.error("Brevo requests send failed: %s", e)
		raise
