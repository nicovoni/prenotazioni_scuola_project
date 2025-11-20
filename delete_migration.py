#!/usr/bin/env python

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    # Delete the migration record if it exists
    cursor.execute("DELETE FROM django_migrations WHERE app = 'prenotazioni' AND name = '0001_initial'")
    print("Deleted prenotazioni migration record")

    # Clean up any content types with null name to fix IntegrityError
    cursor.execute("DELETE FROM django_content_type WHERE name IS NULL")
    print("Cleaned up bad content type records")
