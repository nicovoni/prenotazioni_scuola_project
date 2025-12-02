"""Merge migration to resolve multiple leaf nodes between 0002 and 0005.

This file was created manually to match what `python manage.py makemigrations --merge`
would generate on the deployment server. It creates an empty migration that depends
on both conflicting migrations so Django's migration graph has a single leaf.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0002_add_password_fields'),
        ('prenotazioni', '0005_add_password_fields_and_history'),
    ]

    operations = []
