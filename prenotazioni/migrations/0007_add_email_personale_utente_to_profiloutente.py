from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('prenotazioni', '0006_add_telefono_utente_to_profiloutente'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiloutente',
            name='email_personale_utente',
            field=models.EmailField(max_length=254, verbose_name='Email Personale Utente', blank=True, default=''),
            preserve_default=False,
        ),
    ]