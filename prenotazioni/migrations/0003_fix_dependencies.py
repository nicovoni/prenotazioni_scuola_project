"""
Fix migration dependencies issue.

This empty migration ensures that both auth.0001_initial and
prenotazioni.0001_initial are applied before any other operations,
forcing the correct order for Render deployments.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('prenotazioni', '0001_initial'),
    ]

    operations = [
        # Empty migration - only purpose is to establish correct dependency order
        # This forces Django to apply auth.0001_initial and prenotazioni.0001_initial
        # in the correct sequence before any other operations
    ]
