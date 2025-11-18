# Generated migration to simplify models by removing unnecessary fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0004_add_device_catalog_and_improvements'),
    ]

    operations = [
        # Update fields from SchoolInfo
        migrations.RenameField(
            model_name='schoolinfo',
            old_name='nome_scuola',
            new_name='nome',
        ),
        migrations.RemoveField(
            model_name='schoolinfo',
            name='email_scuola',
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='codice_meccanografico',
            field=models.CharField(
                blank=True,
                max_length=10,
                null=True,
                verbose_name='Codice meccanografico',
                help_text='Codice meccanografico di identificazione della scuola'
            ),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='sito_web',
            field=models.URLField(
                help_text='URL del sito web della scuola',
                verbose_name='Sito web'
            ),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='indirizzo',
            field=models.TextField(
                help_text='Indirizzo completo della scuola',
                verbose_name='Indirizzo'
            ),
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
