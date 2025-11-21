from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('prenotazioni', '0005_add_altri_campi_to_profiloutente'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiloutente',
            name='telefono_utente',
            field=models.CharField(max_length=30, verbose_name='Telefono Utente', blank=True, default=''),
            preserve_default=False,
        ),
    ]