"""Config package for the prenotazioni-scuola application.

Import Celery app so that `celery` autodiscovery works when Django starts.
"""
try:
	# Ensure Celery app is loaded when Django starts
	from .. import celery as celery_app  # noqa: F401
except Exception:
	# If Celery isn't available in the environment, don't break imports
	pass
