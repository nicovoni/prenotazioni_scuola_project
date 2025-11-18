# Migration to update SchoolInfo fields according to new requirements

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0005_simplify_models'),
    ]

    operations = [
        # Rename nome_scuola to nome
        migrations.RenameField(
            model_name='schoolinfo',
            old_name='nome_scuola',
            new_name='nome',
        ),

        # Remove email_scuola (no longer needed)
        migrations.RemoveField(
            model_name='schoolinfo',
            name='email_scuola',
        ),

        # Add new fields
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
                verbose_name='URL sito web',
                help_text='URL completo del sito web della scuola'
            ),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='indirizzo',
            field=models.TextField(
                verbose_name='Indirizzo completo',
                help_text='Indirizzo completo della scuola secondo lo standard di Google Maps'
            ),
        ),
    ]
