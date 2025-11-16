import os
from django.core.wsgi import get_wsgi_application

# La variabile DJANGO_SETTINGS_MODULE viene impostata nel render.yaml
application = get_wsgi_application()
