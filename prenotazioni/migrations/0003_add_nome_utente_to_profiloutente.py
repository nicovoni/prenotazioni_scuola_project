from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('prenotazioni', '0002_profiloutente'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiloutente',
            name='nome_utente',
            field=models.CharField(max_length=100, verbose_name='Nome Utente', help_text='Nome di battesimo', default=''),
            preserve_default=False,
        ),
    ]