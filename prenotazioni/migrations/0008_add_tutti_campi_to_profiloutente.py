from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('prenotazioni', '0007_add_email_personale_utente_to_profiloutente'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiloutente',
            name='numero_matricola_utente',
            field=models.CharField(max_length=20, blank=True, verbose_name='Numero Matricola Utente', help_text='Per studenti e docenti', default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='classe_utente',
            field=models.CharField(max_length=20, blank=True, verbose_name='Classe/Sezione Utente', help_text='Per studenti (es: 5A, 3B)', default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='dipartimento_utente',
            field=models.CharField(max_length=100, blank=True, verbose_name='Dipartimento Utente', help_text='Per docenti', default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='materia_insegnamento_utente',
            field=models.CharField(max_length=100, blank=True, verbose_name='Materia Insegnamento Utente', help_text='Per docenti', default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='preferenze_notifica_utente',
            field=models.JSONField(default=dict, blank=True, verbose_name='Preferenze Notifica Utente', help_text='Configurazione notifiche personalizzate'),
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='preferenze_lingua_utente',
            field=models.CharField(max_length=10, default='it', verbose_name='Lingua Preferita Utente'),
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='fuso_orario_utente',
            field=models.CharField(max_length=50, default='Europe/Rome', verbose_name='Fuso Orario Utente'),
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='utente_attivo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='utente_verificato',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='data_verifica_utente',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='ultimo_accesso_utente',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='data_creazione_utente',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='data_modifica_utente',
            field=models.DateTimeField(auto_now=True),
        ),
    ]