from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('prenotazioni', '0009_make_personal_fields_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='sessioneutente',
            name='metadati_sessione',
            field=models.JSONField(default=dict, blank=True, verbose_name='Metadati Sessione', help_text='Dati aggiuntivi della sessione'),
        ),
        migrations.AddField(
            model_name='sessioneutente',
            name='email_destinazione_sessione',
            field=models.EmailField(blank=True, null=True, verbose_name='Email Destinazione Sessione', help_text='Email destinatario per notifiche o verifiche'),
        ),
    ]