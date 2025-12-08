# Generated migration for adding first_login field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0007_populate_password_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiloutente',
            name='first_login',
            field=models.BooleanField(
                default=True,
                help_text='Indica se è il primo accesso dell\'utente nel sistema',
                verbose_name='Primo accesso'
            ),
        ),
    ]
