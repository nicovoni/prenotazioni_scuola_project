#!/usr/bin/env python

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'prenotazioni' AND name = '0001_initial'")
    print("Deleted prenotazioni migration record")
