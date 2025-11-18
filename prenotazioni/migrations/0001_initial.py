# Generated migration for initial models
from django.contrib.auth.models import User
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(help_text='Nome commerciale completo (es. "iPad Pro 12.9" o "Dell Latitude 5420")', max_length=100, verbose_name='Nome dispositivo')),
                ('tipo', models.CharField(choices=[('notebook', 'Notebook/Portatile'), ('tablet', 'Tablet'), ('chromebook', 'Chromebook'), ('altro', 'Altro')], help_text='Categoria generale del dispositivo', max_length=20, verbose_name='Tipo dispositivo')),
                ('produttore', models.CharField(help_text='Azienda produttrice del dispositivo', max_length=100, verbose_name='Produttore')),
                ('modello', models.CharField(blank=True, help_text='Modello specifico del dispositivo', max_length=100, verbose_name='Modello')),
                ('attivo', models.BooleanField(default=True, help_text='Dispositivo disponibile per l\'uso nei carrelli', verbose_name='Attivo')),
            ],
            options={
                'verbose_name': 'Dispositivo',
                'verbose_name_plural': 'Dispositivi',
                'ordering': ['produttore', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='SchoolInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(help_text='Nome completo e formale della scuola', max_length=200, verbose_name='Nome completo scuola')),
                ('codice_meccanografico', models.CharField(help_text='Codice meccanografico di identificazione della scuola', max_length=10, verbose_name='Codice meccanografico')),
                ('sito_web', models.URLField(help_text='URL completo del sito web della scuola', verbose_name='URL sito web')),
                ('indirizzo', models.TextField(help_text='Indirizzo completo della scuola secondo lo standard di Google Maps', verbose_name='Indirizzo completo')),
            ],
            options={
                'verbose_name': 'Informazioni scuola',
                'verbose_name_plural': 'Informazioni scuola',
            },
        ),
        migrations.CreateModel(
            name='Utente',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='auth.user')),
                ('ruolo', models.CharField(choices=[('docente', 'Docente'), ('studente', 'Studente'), ('assistente', 'Assistente tecnico'), ('admin', 'Amministratore')], default='studente', help_text='Ruolo dell\'utente nel sistema scolastico', max_length=20, verbose_name='Ruolo')),
            ],
            options={
                'verbose_name': 'Utente',
                'verbose_name_plural': 'Utenti',
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Risorsa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(help_text='Nome identificativo della risorsa', max_length=100, verbose_name='Nome risorsa')),
                ('tipo', models.CharField(choices=[('lab', 'Laboratorio'), ('carrello', 'Carrello')], help_text='Tipo di risorsa (laboratorio o carrello)', max_length=20, verbose_name='Tipo')),
                ('capacita_massima', models.PositiveIntegerField(blank=True, help_text='Per carrelli: numero massimo di dispositivi prenotabili contemporaneamente', null=True, verbose_name='Capacità massima')),
                ('descrizione', models.TextField(blank=True, help_text='Informazioni aggiuntive sulla risorsa (opzionale, max 500 caratteri)', verbose_name='Descrizione')),
                ('attiva', models.BooleanField(default=True, help_text='Risorsa disponibile per prenotazioni', verbose_name='Attiva')),
                ('dispositivi', models.ManyToManyField(blank=True, related_name='risorse', to='prenotazioni.device', verbose_name='Dispositivi disponibili')),
            ],
            options={
                'verbose_name': 'Risorsa',
                'verbose_name_plural': 'Risorse',
                'ordering': ['tipo', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='Prenotazione',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantita', models.PositiveIntegerField(default=1, help_text='Numero di postazioni/dispositivi richiesti', verbose_name='Quantità')),
                ('inizio', models.DateTimeField(help_text='Inizio del periodo di prenotazione', verbose_name='Data/ora inizio')),
                ('fine', models.DateTimeField(help_text='Fine del periodo di prenotazione', verbose_name='Data/ora fine')),
                ('attiva', models.BooleanField(default=True, help_text='Prenotazione attiva (può essere disabilitata da admin)', verbose_name='Attiva')),
                ('creato_il', models.DateTimeField(auto_now_add=True, verbose_name='Creato il')),
                ('modificato_il', models.DateTimeField(auto_now=True, verbose_name='Modificato il')),
                ('risorsa', models.ForeignKey(help_text='Risorsa prenotata', on_delete=django.db.models.deletion.CASCADE, to='prenotazioni.risorsa', verbose_name='Risorsa')),
                ('utente', models.ForeignKey(help_text='Utente che ha effettuato la prenotazione', on_delete=django.db.models.deletion.CASCADE, to='prenotazioni.utente', verbose_name='Utente')),
            ],
            options={
                'verbose_name': 'Prenotazione',
                'verbose_name_plural': 'Prenotazioni',
                'ordering': ['-inizio'],
            },
        ),
        # Add constraints and indexes
        migrations.AddConstraint(
            model_name='device',
            constraint=models.CheckConstraint(check=models.Q(nome__regex='^[A-Za-z0-9\\s\\-\\.]+$'), name='device_name_valid_chars'),
        ),
        migrations.AddConstraint(
            model_name='device',
            constraint=models.CheckConstraint(check=models.Q(produttore__regex='^[A-Za-z0-9\\s\\-\\.]+$'), name='device_produttore_valid_chars'),
        ),
        migrations.AddConstraint(
            model_name='device',
            constraint=models.UniqueConstraint(condition=models.Q(modello__gt='', modello__isnull=False), fields=('nome', 'modello'), name='unique_device_name_model'),
        ),
        migrations.AddConstraint(
            model_name='prenotazione',
            constraint=models.CheckConstraint(check=models.Q(fine__gt=models.F('inizio')), name='prenotazione_fine_dopo_inizio'),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['produttore', 'nome'], name='prenotazioni_dev_produttore_nome_idx'),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['tipo', 'attivo'], name='prenotazioni_dev_tipo_attivo_idx'),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['nome'], name='prenotazioni_dev_nome_idx'),
        ),
        migrations.AddIndex(
            model_name='prenotazione',
            index=models.Index(fields=['inizio', 'fine'], name='prenotazioni_pre_inizio_fine_idx'),
        ),
        migrations.AddIndex(
            model_name='prenotazione',
            index=models.Index(fields=['risorsa', 'inizio', 'fine'], name='prenotazioni_pre_risorsa_inizio_fine_idx'),
        ),
        migrations.AddIndex(
            model_name='prenotazione',
            index=models.Index(fields=['utente', '-inizio'], name='prenotazioni_pre_utente_inizio_idx'),
        ),
        migrations.AddIndex(
            model_name='prenotazione',
            index=models.Index(fields=['attiva'], name='prenotazioni_pre_attiva_idx'),
        ),
        migrations.AddIndex(
            model_name='risorsa',
            index=models.Index(fields=['tipo', 'attiva'], name='prenotazioni_ris_tipo_attiva_idx'),
        ),
        migrations.AddIndex(
            model_name='risorsa',
            index=models.Index(fields=['nome'], name='prenotazioni_ris_nome_idx'),
        ),
    ]
