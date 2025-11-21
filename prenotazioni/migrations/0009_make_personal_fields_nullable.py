from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('prenotazioni', '0008_add_tutti_campi_to_profiloutente'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profiloutente',
            name='nome_utente',
            field=models.CharField(max_length=100, verbose_name='Nome Utente', help_text='Nome di battesimo', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profiloutente',
            name='cognome_utente',
            field=models.CharField(max_length=100, verbose_name='Cognome Utente', help_text='Cognome', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profiloutente',
            name='sesso_utente',
            field=models.CharField(max_length=10, choices=[('M', 'Maschio'), ('F', 'Femmina'), ('ALTRO', 'Altro')], blank=True, null=True, verbose_name='Sesso Utente'),
        ),
        migrations.AlterField(
            model_name='profiloutente',
            name='codice_fiscale_utente',
            field=models.CharField(max_length=16, blank=True, null=True, verbose_name='Codice Fiscale Utente'),
        ),
        migrations.AlterField(
            model_name='profiloutente',
            name='telefono_utente',
            field=models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefono Utente'),
        ),
        migrations.AlterField(
            model_name='profiloutente',
            name='email_personale_utente',
            field=models.EmailField(blank=True, null=True, verbose_name='Email Personale Utente', help_text='Email alternativa per comunicazioni'),
        ),
    ]