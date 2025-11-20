"""
Initial migration stub - sarà sostituita durante makemigrations del deploy.

Questa migrazione vuota è necessaria per indicare che il sistema
sa delle migrazioni, anche se verranno rigenerate automaticamente
durante il deploy.
"""

from django.db import migrations


class Migration(migrations.Migration):
    """
    Migrazione iniziale stub per prenotazioni.
    Sarà automaticamente rigenerata durante makemigrations nel build.
    """

    dependencies = []

    operations = [
        # Le operazioni reali verranno generate automaticamente
        # durante python manage.py makemigrations
    ]
