import os
import sys
from django.core.wsgi import get_wsgi_application

# Aggiungi il path del progetto per trovare i moduli
sys.path.insert(0, '/app')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
application = get_wsgi_application()
