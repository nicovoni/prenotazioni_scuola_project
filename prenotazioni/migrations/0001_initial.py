# Generated migration for the completely renewed architecture

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chiave', models.CharField(max_length=100, unique=True, verbose_name='Chiave configurazione')),
                ('valore', models.TextField(verbose_name='Valore')),
                ('tipo', models.CharField(choices=[('email', 'Email/SMTP'), ('booking', 'Prenotazioni'), ('system', 'Sistema'), ('ui', 'Interfaccia'), ('security', 'Sicurezza')], max_length=20, verbose_name='Tipo configurazione')),
                ('descrizione', models.TextField(blank=True, verbose_name='Descrizione')),
                ('modificabile', models.BooleanField(default=True, verbose_name='Modificabile')),
                ('creato_il', models.DateTimeField(auto_now_add=True)),
                ('modificato_il', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configurazione',
                'verbose_name_plural': 'Configurazioni',
                'ordering': ['tipo', 'chiave'],
            },
        ),
        migrations.CreateModel(
            name='SchoolInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_completo', models.CharField(max_length=200, verbose_name='Nome completo scuola')),
                ('nome_breve', models.CharField(max_length=100, verbose_name='Nome breve')),
                ('codice_meccanografico', models.CharField(max_length=10, unique=True, verbose_name='Codice meccanografico')),
                ('partita_iva', models.CharField(blank=True, max_length=20, verbose_name='Partita IVA')),
                ('sito_web', models.URLField(verbose_name='URL sito web')),
                ('email_istituzionale', models.EmailField(verbose_name='Email istituzionale')),
                ('telefono', models.CharField(blank=True, max_length=20, verbose_name='Telefono')),
                ('fax', models.CharField(blank=True, max_length=20, verbose_name='Fax')),
                ('indirizzo', models.TextField(verbose_name='Indirizzo completo')),
                ('cap', models.CharField(max_length=10, verbose_name='CAP')),
                ('comune', models.CharField(max_length=100, verbose_name='Comune')),
                ('provincia', models.CharField(max_length=50, verbose_name='Provincia')),
                ('regione', models.CharField(max_length=50, verbose_name='Regione')),
                ('nazione', models.CharField(default='Italia', max_length=50, verbose_name='Nazione')),
                ('latitudine', models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True, verbose_name='Latitudine')),
                ('longitudine', models.DecimalField(blank=True, decimal_places=8, max_digits=11, null=True, verbose_name='Longitudine')),
                ('attivo', models.BooleanField(default=True)),
                ('creato_il', models.DateTimeField(auto_now_add=True)),
                ('modificato_il', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Informazioni Scuola',
                'verbose_name_plural': 'Informazioni Scuola',
            },
        ),
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('email_verification', 'Verifica Email'), ('password_reset', 'Reset Password'), ('pin_login', 'Login con PIN'), ('admin_setup', 'Setup Amministratore'), ('booking_confirmation', 'Conferma Prenotazione')], max_length=30, verbose_name='Tipo Sessione')),
                ('token', models.UUIDField(default=uuid.uuid4, unique=True, verbose_name='Token Unico')),
                ('pin', models.CharField(blank=True, max_length=6, verbose_name='PIN')),
                ('stato', models.CharField(choices=[('pending', 'In Attesa'), ('verified', 'Verificato'), ('expired', 'Scaduto'), ('cancelled', 'Annullato'), ('failed', 'Fallito')], default='pending', max_length=20, verbose_name='Stato')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadati')),
                ('email_destinazione', models.EmailField(verbose_name='Email Destinazione')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Sessione Utente',
                'verbose_name_plural': 'Sessioni Utente',
            },
        ),
        migrations.CreateModel(
            name='DeviceCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, unique=True)),
                ('descrizione', models.TextField(blank=True)),
                ('icona', models.CharField(blank=True, max_length=50)),
                ('colore', models.CharField(default='#007bff', max_length=7)),
                ('attiva', models.BooleanField(default=True)),
                ('ordine', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Categoria Dispositivo',
                'verbose_name_plural': 'Categorie Dispositivi',
                'ordering': ['ordine', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='ResourceLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, unique=True)),
                ('descrizione', models.TextField(blank=True)),
                ('edificio', models.CharField(max_length=50)),
                ('piano', models.CharField(max_length=20)),
                ('aula', models.CharField(max_length=50)),
                ('capacita_persone', models.PositiveIntegerField(default=0)),
                ('attrezzature_presenti', models.JSONField(blank=True, default=list)),
                ('coordinate_x', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('coordinate_y', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('attivo', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Localizzazione',
                'verbose_name_plural': 'Localizzazioni',
                'ordering': ['edificio', 'piano', 'aula'],
            },
        ),
        migrations.CreateModel(
            name='BookingStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, unique=True)),
                ('descrizione', models.TextField()),
                ('colore', models.CharField(default='#007bff', max_length=7)),
                ('icon', models.CharField(blank=True, max_length=50)),
                ('ordine', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Stato Prenotazione',
                'verbose_name_plural': 'Stati Prenotazioni',
                'ordering': ['ordine'],
            },
        ),
        migrations.CreateModel(
            name='SystemLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('livello', models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Informazione'), ('WARNING', 'Avviso'), ('ERROR', 'Errore'), ('CRITICAL', 'Critico')], default='INFO', max_length=10)),
                ('tipo_evento', models.CharField(choices=[('user_login', 'Login Utente'), ('user_logout', 'Logout Utente'), ('user_registration', 'Registrazione'), ('booking_created', 'Prenotazione Creata'), ('booking_modified', 'Prenotazione Modificata'), ('booking_cancelled', 'Prenotazione Cancellata'), ('booking_approved', 'Prenotazione Approvata'), ('device_assigned', 'Dispositivo Assegnato'), ('resource_created', 'Risorsa Creata'), ('config_changed', 'Configurazione Modificata'), ('system_error', 'Errore Sistema'), ('security_event', 'Eventi Sicurezza'), ('email_sent', 'Email Inviata'), ('data_export', 'Esportazione Dati'), ('backup_created', 'Backup Creato')], max_length=30)),
                ('messaggio', models.TextField(verbose_name='Messaggio')),
                ('dettagli', models.JSONField(blank=True, default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('request_path', models.CharField(blank=True, max_length=200)),
                ('metodo_http', models.CharField(blank=True, max_length=10)),
                ('object_type', models.CharField(blank=True, max_length=50)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Log Sistema',
                'verbose_name_plural': 'Log Sistema',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, unique=True)),
                ('tipo', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS'), ('push', 'Notifica Push'), ('in_app', 'In-App')], max_length=20)),
                ('evento', models.CharField(max_length=50)),
                ('oggetto', models.CharField(max_length=200)),
                ('contenuto', models.TextField()),
                ('attivo', models.BooleanField(default=True)),
                ('invio_immediato', models.BooleanField(default=True)),
                ('tentativi_massimi', models.PositiveIntegerField(default=3)),
                ('intervallo_tentativi_minuti', models.PositiveIntegerField(default=15)),
                ('variabili_disponibili', models.JSONField(default=list)),
                ('creato_il', models.DateTimeField(auto_now_add=True)),
                ('modificato_il', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Template Notifica',
                'verbose_name_plural': 'Template Notifiche',
            },
        ),
        migrations.CreateModel(
            name='FileUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploads/%Y/%m/%d/')),
                ('nome_originale', models.CharField(max_length=255)),
                ('dimensione', models.PositiveIntegerField()),
                ('tipo_mime', models.CharField(max_length=100)),
                ('tipo_file', models.CharField(choices=[('document', 'Documento'), ('image', 'Immagine'), ('video', 'Video'), ('audio', 'Audio'), ('archive', 'Archivio'), ('other', 'Altro')], max_length=20)),
                ('titolo', models.CharField(blank=True, max_length=200)),
                ('descrizione', models.TextField(blank=True)),
                ('tags', models.JSONField(blank=True, default=list)),
                ('checksum', models.CharField(blank=True, max_length=64)),
                ('virus_scanned', models.BooleanField(default=False)),
                ('scan_result', models.CharField(blank=True, max_length=20)),
                ('pubblico', models.BooleanField(default=False)),
                ('attivo', models.BooleanField(default=True)),
                ('download_count', models.PositiveIntegerField(default=0)),
                ('ultimo_download', models.DateTimeField(blank=True, null=True)),
                ('creato_il', models.DateTimeField(auto_now_add=True)),
                ('modificato_il', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'File Caricato',
                'verbose_name_plural': 'File Caricati',
                'ordering': ['-creato_il'],
            },
        ),
    ]
