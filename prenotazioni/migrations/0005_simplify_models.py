# Generated migration to simplify models by removing unnecessary fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0004_add_device_catalog_and_improvements'),
    ]

    operations = [
        # Remove fields from SchoolInfo
        migrations.RemoveField(
            model_name='schoolinfo',
            name='indirizzo',
        ),
        migrations.RemoveField(
            model_name='schoolinfo',
            name='telefono',
        ),
        migrations.RemoveField(
            model_name='schoolinfo',
            name='sito_web',
        ),
        migrations.RemoveField(
            model_name='schoolinfo',
            name='codice_scuola',
        ),

        # Remove fields from Device
        migrations.RemoveField(
            model_name='device',
            name='sistema_operativo',
        ),
        migrations.RemoveField(
            model_name='device',
            name='tipo_display',
        ),
        migrations.RemoveField(
            model_name='device',
            name='processore',
        ),
        migrations.RemoveField(
            model_name='device',
            name='storage',
        ),
        migrations.RemoveField(
            model_name='device',
            name='schermo',
        ),
        migrations.RemoveField(
            model_name='device',
            name='caratteristiche_extra',
        ),

        # Alter produttore field in Device to remove choices
        migrations.AlterField(
            model_name='device',
            name='produttore',
            field=models.CharField(max_length=100, verbose_name='Produttore'),
        ),

        # Remove fields from Utente
        migrations.RemoveField(
            model_name='utente',
            name='telefono',
        ),
        migrations.RemoveField(
            model_name='utente',
            name='classe',
        ),
    ]
