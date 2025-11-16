# Gunicorn configuration optimized for Render free tier (512MB RAM)
workers = 2
threads = 1  # Ridotto per free tier
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2  # Ridotto
preload_app = True  # Aggiunto per efficiency
loglevel = 'warning'  # Meno verboso in produzione
