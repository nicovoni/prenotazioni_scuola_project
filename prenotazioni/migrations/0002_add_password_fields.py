"""No-op migration.

This migration used to add password-related fields and the PasswordHistory model.
Those operations are implemented in `0005_add_password_fields_and_history.py` in
this repository. To avoid duplicate-column errors during deploy (where 0005 may
be applied before 0002), this file has been converted to a no-op so the
migration graph can be linearized safely.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = []
