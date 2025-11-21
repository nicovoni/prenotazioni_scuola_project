from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('prenotazioni', '0003_add_nome_utente_to_profiloutente'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiloutente',
            name='cognome_utente',
            field=models.CharField(max_length=100, verbose_name='Cognome Utente', help_text='Cognome', default=''),
            preserve_default=False,
        ),
    ]