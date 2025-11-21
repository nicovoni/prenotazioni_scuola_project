from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfiloUtente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('utente', models.ForeignKey('auth.User', on_delete=models.CASCADE)),
                ('nome', models.CharField(max_length=100)),
                # Aggiungi qui altri campi definiti nel modello ProfiloUtente
            ],
        ),
    ]