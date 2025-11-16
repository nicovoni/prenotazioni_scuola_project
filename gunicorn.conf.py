# Gunicorn configuration optimized for Render free tier (512MB RAM)
workers = 2
threads = 2
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 10
loglevel = 'info'
