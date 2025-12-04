from django.db import migrations


def create_password_history(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    PasswordHistory = apps.get_model('prenotazioni', 'PasswordHistory')
    from django.conf import settings

    keep = int(getattr(settings, 'PASSWORD_HISTORY_COUNT', 5))

    for user in User.objects.all():
        try:
            # If user already has history, skip
            if PasswordHistory.objects.filter(utente_id=user.id).exists():
                continue
            # Create a single history record from current password hash
            if user.password:
                PasswordHistory.objects.create(utente_id=user.id, password_hash=user.password)
                # prune if somehow more than keep
                qs = PasswordHistory.objects.filter(utente_id=user.id).order_by('-created_at')
                if qs.count() > keep:
                    for ph in qs[keep:]:
                        ph.delete()
        except Exception:
            # Do not fail migration for individual user errors
            continue


class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0006_merge_0002_0005'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_password_history, reverse_code=migrations.RunPython.noop),
    ]
