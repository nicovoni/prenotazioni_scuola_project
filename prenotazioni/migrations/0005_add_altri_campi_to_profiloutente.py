from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('prenotazioni', '0004_add_cognome_utente_to_profiloutente'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiloutente',
            name='sesso_utente',
            field=models.CharField(max_length=10, choices=[('M', 'Maschio'), ('F', 'Femmina'), ('ALTRO', 'Altro')], blank=True, verbose_name='Sesso Utente', default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='data_nascita_utente',
            field=models.DateField(null=True, blank=True, verbose_name='Data Nascita Utente'),
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='codice_fiscale_utente',
            field=models.CharField(max_length=100, verbose_name='Codice Fiscale Utente', blank=True, default=''),
            preserve_default=False,
        ),
    ]