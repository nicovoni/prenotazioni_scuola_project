# Migration to add SchoolInfo model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0002_create_initial_resources'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_scuola', models.CharField(help_text='Nome completo della scuola', max_length=200, verbose_name='Nome della scuola')),
                ('indirizzo', models.TextField(blank=True, help_text='Indirizzo completo della scuola', null=True, verbose_name='Indirizzo')),
                ('telefono', models.CharField(blank=True, help_text='Numero di telefono della scuola', max_length=20, null=True, verbose_name='Telefono')),
                ('email_scuola', models.EmailField(blank=True, help_text='Indirizzo email principale della scuola', max_length=254, null=True, verbose_name='Email della scuola')),
                ('sito_web', models.URLField(blank=True, help_text='URL del sito web della scuola', null=True, verbose_name='Sito web')),
                ('codice_scuola', models.CharField(blank=True, help_text='Codice identificativo della scuola (es. codice meccanografico)', max_length=20, null=True, verbose_name='Codice scuola')),
            ],
            options={
                'verbose_name': 'Informazioni scuola',
                'verbose_name_plural': 'Informazioni scuola',
            },
        ),
    ]
