# 🛠️ SOLUZIONI ALTERNATIVE - RISOLUZIONE DATABASE RENDER.COM

## Problema Confermato
- ❌ **Tabella "prenotazioni_utente" non esiste**
- ❌ **Sito https://prenotazioni-scuola.onrender.com non funzionale**
- ❌ **Database Neon con migrazione incompleta**

---

## ⚡ SOLUZIONI PER RENDER.COM (SENZA ACCESSO LOCALE)

### 🎯 OPZIONE 1: Modifica File GitHub + Redeploy

#### Step 1: Modifica la migrazione su GitHub
Crea un nuovo file `prenotazioni/migrations/0001_initial_fixed.py`:

```python
# Generated migration FIXED per migrazione completa
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone
import uuid

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Configuration
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('chiave', models.CharField(max_length=100, unique=True)),
                ('valore', models.TextField()),
                ('tipo', models.CharField(max_length=20, choices=[
                    ('email', 'Email/SMTP'),
                    ('booking', 'Prenotazioni'),
                    ('system', 'Sistema'),
                    ('ui', 'Interfaccia'),
                    ('security', 'Sicurezza'),
                ])),
                ('descrizione', models.TextField(blank=True)),
                ('modificabile', models.BooleanField(default=True)),
                ('creato_il', models.DateTimeField(auto_now_add=True)),
                ('modificato_il', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configurazione',
                'verbose_name_plural': 'Configurazioni',
                'ordering': ['tipo', 'chiave'],
            },
        ),
        
        # SchoolInfo
        migrations.CreateModel(
            name='SchoolInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nome_completo', models.CharField(max_length=200)),
                ('nome_breve', models.CharField(max_length=100)),
                ('codice_meccanografico', models.CharField(max_length=10, unique=True)),
                ('partita_iva', models.CharField(max_length=20, blank=True)),
                ('sito_web', models.URLField()),
                ('email_istituzionale', models.EmailField()),
                ('telefono', models.CharField(max_length=20, blank=True)),
                ('fax', models.CharField(max_length=20, blank=True)),
                ('indirizzo', models.TextField()),
                ('cap', models.CharField(max_length=10)),
                ('comune', models.CharField(max_length=100)),
                ('provincia', models.CharField(max_length=50)),
                ('regione', models.CharField(max_length=50)),
                ('nazione', models.CharField(max_length=50, default='Italia')),
                ('latitudine', models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)),
                ('longitudine', models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)),
                ('attivo', models.BooleanField(default=True)),
                ('creato_il', models.DateTimeField(auto_now_add=True)),
                ('modificato_il', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Informazioni Scuola',
                'verbose_name_plural': 'Informazioni Scuola',
            },
        ),
        
        # DeviceCategory
        migrations.CreateModel(
            name='DeviceCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=100, unique=True)),
                ('descrizione', models.TextField(blank=True)),
                ('icona', models.CharField(max_length=50, blank=True)),
                ('colore', models.CharField(max_length=7, default='#007bff')),
                ('attiva', models.BooleanField(default=True)),
                ('ordine', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Categoria Dispositivo',
                'verbose_name_plural': 'Categorie Dispositivi',
                'ordering': ['ordine', 'nome'],
            },
        ),
        
        # ResourceLocation
        migrations.CreateModel(
            name='ResourceLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=100, unique=True)),
                ('descrizione', models.TextField(blank=True)),
                ('edificio', models.CharField(max_length=50)),
                ('piano', models.CharField(max_length=20)),
                ('aula', models.CharField(max_length=50)),
                ('capacita_persone', models.PositiveIntegerField(default=0)),
                ('attrezzature_presenti', models.JSONField(default=list, blank=True)),
                ('coordinate_x', models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)),
                ('coordinate_y', models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)),
                ('attivo', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Localizzazione',
                'verbose_name_plural': 'Localizzazioni',
                'ordering': ['edificio', 'piano', 'aula'],
            },
        ),
        
        # BookingStatus
        migrations.CreateModel(
            name='BookingStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=50, unique=True)),
                ('descrizione', models.TextField()),
                ('colore', models.CharField(max_length=7, default='#007bff')),
                ('icon', models.CharField(max_length=50, blank=True)),
                ('ordine', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Stato Prenotazione',
                'verbose_name_plural': 'Stati Prenotazioni',
                'ordering': ['ordine'],
            },
        ),
        
        # SystemLog
        migrations.CreateModel(
            name='SystemLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('livello', models.CharField(max_length=10, choices=[
                    ('DEBUG', 'Debug'),
                    ('INFO', 'Informazione'),
                    ('WARNING', 'Avviso'),
                    ('ERROR', 'Errore'),
                    ('CRITICAL', 'Critico'),
                ], default='INFO')),
                ('tipo_evento', models.CharField(max_length=30)),
                ('messaggio', models.TextField()),
                ('dettagli', models.JSONField(default=dict, blank=True)),
                ('ip_address', models.GenericIPAddressField(null=True, blank=True)),
                ('user_agent', models.TextField(blank=True)),
                ('request_path', models.CharField(max_length=200, blank=True)),
                ('metodo_http', models.CharField(max_length=10, blank=True)),
                ('object_type', models.CharField(max_length=50, blank=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Log Sistema',
                'verbose_name_plural': 'Log Sistema',
                'ordering': ['-timestamp'],
            },
            bases=(models.Model,),
        ),
        
        # UserSession
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('tipo', models.CharField(max_length=30, choices=[
                    ('email_verification', 'Verifica Email'),
                    ('password_reset', 'Reset Password'),
                    ('pin_login', 'Login con PIN'),
                    ('admin_setup', 'Setup Amministratore'),
                    ('booking_confirmation', 'Conferma Prenotazione'),
                ])),
                ('token', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('pin', models.CharField(max_length=6, blank=True)),
                ('stato', models.CharField(max_length=20, choices=[
                    ('pending', 'In Attesa'),
                    ('verified', 'Verificato'),
                    ('expired', 'Scaduto'),
                    ('cancelled', 'Annullato'),
                    ('failed', 'Fallito'),
                ], default='pending')),
                ('metadata', models.JSONField(default=dict, blank=True)),
                ('email_destinazione', models.EmailField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('verified_at', models.DateTimeField(null=True, blank=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Sessione Utente',
                'verbose_name_plural': 'Sessioni Utente',
            },
            bases=(models.Model,),
        ),
        
        # Device
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=100)),
                ('modello', models.CharField(max_length=100, blank=True)),
                ('marca', models.CharField(max_length=100)),
                ('serie', models.CharField(max_length=100, blank=True)),
                ('codice_inventario', models.CharField(max_length=50, unique=True)),
                ('tipo', models.CharField(max_length=20, choices=[
                    ('laptop', 'Laptop/Notebook'),
                    ('desktop', 'Computer Desktop'),
                    ('tablet', 'Tablet'),
                    ('smartphone', 'Smartphone'),
                    ('projector', 'Proiettore'),
                    ('smartboard', 'Lavagna Interattiva'),
                    ('camera', 'Videocamera'),
                    ('audio', 'Attrezzatura Audio'),
                    ('network', 'Attrezzatura Rete'),
                    ('altro', 'Altro'),
                ])),
                ('specifiche', models.JSONField(default=dict, blank=True)),
                ('stato', models.CharField(max_length=20, default='disponibile', choices=[
                    ('disponibile', 'Disponibile'),
                    ('in_uso', 'In Uso'),
                    ('manutenzione', 'In Manutenzione'),
                    ('danneggiato', 'Danneggiato'),
                    ('smarrito', 'Smarrito'),
                    ('ritirato', 'Ritirato'),
                ])),
                ('attivo', models.BooleanField(default=True)),
                ('edificio', models.CharField(max_length=50, blank=True)),
                ('piano', models.CharField(max_length=20, blank=True)),
                ('aula', models.CharField(max_length=50, blank=True)),
                ('armadio', models.CharField(max_length=50, blank=True)),
                ('data_acquisto', models.DateField(null=True, blank=True)),
                ('data_scadenza_garanzia', models.DateField(null=True, blank=True)),
                ('valore_acquisto', models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)),
                ('note', models.TextField(blank=True)),
                ('ultimo_controllo', models.DateTimeField(null=True, blank=True)),
                ('prossima_manutenzione', models.DateTimeField(null=True, blank=True)),
                ('creato_il', models.DateTimeField(auto_now_add=True)),
                ('modificato_il', models.DateTimeField(auto_now=True)),
                ('categoria', models.ForeignKey(
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True,
                    to='prenotazioni.devicecategory',
                )),
            ],
            options={
                'verbose_name': 'Dispositivo',
                'verbose_name_plural': 'Dispositivi',
                'ordering': ['tipo', 'marca', 'nome'],
            },
            bases=(models.Model,),
        ),
        
        # Resource
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=100)),
                ('codice', models.CharField(max_length=20, unique=True)),
                ('descrizione', models.TextField(blank=True)),
                ('tipo', models.CharField(max_length=20, choices=[
                    ('laboratorio', 'Laboratorio'),
                    ('aula', 'Aula'),
                    ('carrello', 'Carrello Dispositivi'),
                    ('spazio', 'Spazio Comune'),
                    ('attrezzatura', 'Attrezzatura Speciale'),
                    ('ambiente', 'Ambiente Esterno'),
                ])),
                ('categoria', models.CharField(max_length=50, blank=True)),
                ('capacita_massima', models.PositiveIntegerField(null=True, blank=True)),
                ('postazioni_disponibili', models.PositiveIntegerField(default=0)),
                ('orari_apertura', models.JSONField(default=dict, blank=True)),
                ('feriali_disponibile', models.BooleanField(default=True)),
                ('weekend_disponibile', models.BooleanField(default=False)),
                ('festivo_disponibile', models.BooleanField(default=False)),
                ('attivo', models.BooleanField(default=True)),
                ('manutenzione', models.BooleanField(default=False)),
                ('bloccato', models.BooleanField(default=False)),
                ('prenotazione_anticipo_minimo', models.PositiveIntegerField(default=1)),
                ('prenotazione_anticipo_massimo', models.PositiveIntegerField(default=30)),
                ('durata_minima_minuti', models.PositiveIntegerField(default=30)),
                ('durata_massima_minuti', models.PositiveIntegerField(default=240)),
                ('allow_overbooking', models.BooleanField(default=False)),
                ('overbooking_limite', models.PositiveIntegerField(default=0)),
                ('note_amministrative', models.TextField(blank=True)),
                ('note_utenti', models.TextField(blank=True)),
                ('creato_il', models.DateTimeField(auto_now_add=True)),
                ('modificato_il', models.DateTimeField(auto_now=True)),
                ('localizzazione', models.ForeignKey(
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True,
                    to='prenotazioni.resourcelocation',
                )),
            ],
            options={
                'verbose_name': 'Risorsa',
                'verbose_name_plural': 'Risorse',
                'ordering': ['tipo', 'nome'],
            },
            bases=(models.Model,),
        ),
        
        # UserProfile
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=100)),
                ('cognome', models.CharField(max_length=100)),
                ('sesso', models.CharField(max_length=10, blank=True, choices=[
                    ('M', 'Maschio'),
                    ('F', 'Femmina'),
                    ('ALTRO', 'Altro'),
                ])),
                ('data_nascita', models.DateField(null=True, blank=True)),
                ('codice_fiscale', models.CharField(max_length=16, blank=True)),
                ('telefono', models.CharField(max_length=20, blank=True)),
                ('email_personale', models.EmailField(blank=True)),
                ('numero_matricola', models.CharField(max_length=20, blank=True)),
                ('classe', models.CharField(max_length=20, blank=True)),
                ('dipartimento', models.CharField(max_length=100, blank=True)),
                ('materia_insegnamento', models.CharField(max_length=100, blank=True)),
                ('preferenze_notifica', models.JSONField(default=dict, blank=True)),
                ('preferenze_lingua', models.CharField(max_length=10, default='it')),
                ('fuso_orario', models.CharField(max_length=50, default='Europe/Rome')),
                ('attivo', models.BooleanField(default=True)),
                ('verificato', models.BooleanField(default=False)),
                ('data_verifica', models.DateTimeField(null=True, blank=True)),
                ('ultimo_accesso', models.DateTimeField(null=True, blank=True)),
                ('creato_il', models.DateTimeField(auto_now_add=True)),
                ('modificato_il', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Profilo Utente',
                'verbose_name_plural': 'Profili Utenti',
            },
            bases=(models.Model,),
        ),
        
        # NotificationTemplate
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=100, unique=True)),
                ('tipo', models.CharField(max_length=20, choices=[
                    ('email', 'Email'),
                    ('sms', 'SMS'),
                    ('push', 'Notifica Push'),
                    ('in_app', 'In-App'),
                ])),
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
            bases=(models.Model,),
        ),
        
        # Notification
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('tipo', models.CharField(max_length=20)),
                ('canale', models.CharField(max_length=20)),
                ('titolo', models.CharField(max_length=200, blank=True)),
                ('messaggio', models.TextField()),
                ('dati_aggiuntivi', models.JSONField(default=dict, blank=True)),
                ('stato', models.CharField(max_length=20, choices=[
                    ('pending', 'In Coda'),
                    ('sent', 'Inviata'),
                    ('delivered', 'Consegnata'),
                    ('failed', 'Fallita'),
                    ('cancelled', 'Annullata'),
                ], default='pending')),
                ('tentativo_corrente', models.PositiveIntegerField(default=0)),
                ('ultimo_tentativo', models.DateTimeField(null=True, blank=True)),
                ('prossimo_tentativo', models.DateTimeField(null=True, blank=True)),
                ('inviata_il', models.DateTimeField(null=True, blank=True)),
                ('consegnata_il', models.DateTimeField(null=True, blank=True)),
                ('errore_messaggio', models.TextField(blank=True)),
                ('creato_il', models.DateTimeField(auto_now_add=True)),
                ('utente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifiche',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('template', models.ForeignKey(
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True,
                    to='prenotazioni.notificationtemplate',
                )),
            ],
            options={
                'verbose_name': 'Notifica',
                'verbose_name_plural': 'Notifiche',
                'ordering': ['-creato_il'],
            },
            bases=(models.Model,),
        ),
        
        # FileUpload
        migrations.CreateModel(
            name='FileUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to='uploads/%Y/%m/%d/')),
                ('nome_originale', models.CharField(max_length=255)),
                ('dimensione', models.PositiveIntegerField()),
                ('tipo_mime', models.CharField(max_length=100)),
                ('tipo_file', models.CharField(max_length=20, choices=[
                    ('document', 'Documento'),
                    ('image', 'Immagine'),
                    ('video', 'Video'),
                    ('audio', 'Audio'),
                    ('archive', 'Archivio'),
                    ('other', 'Altro'),
                ])),
                ('titolo', models.CharField(max_length=200, blank=True)),
                ('descrizione', models.TextField(blank=True)),
                ('tags', models.JSONField(default=list, blank=True)),
                ('checksum', models.CharField(max_length=64, blank=True)),
                ('virus_scanned', models.BooleanField(default=False)),
                ('scan_result', models.CharField(max_length=20, blank=True)),
                ('pubblico', models.BooleanField(default=False)),
                ('attivo', models.BooleanField(default=True)),
                ('download_count', models.PositiveIntegerField(default=0)),
                ('ultimo_download', models.DateTimeField(null=True, blank=True)),
                ('creato_il', models.DateTimeField(auto_now_add=True)),
                ('modificato_il', models.DateTimeField(auto_now=True)),
                ('caricato_da', models.ForeignKey(
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    related_name='file_caricati',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'File Caricato',
                'verbose_name_plural': 'File Caricati',
                'ordering': ['-creato_il'],
            },
            bases=(models.Model,),
        ),
        
        # Add foreign key relationships
        migrations.AddField(
            model_name='booking',
            name='utente',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='prenotazioni',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='risorsa',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='prenotazioni',
                to='prenotazioni.resource',
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='stato',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                null=True, blank=True,
                to='prenotazioni.bookingstatus',
            ),
        ),
        
        # Many-to-Many relationships
        migrations.AddField(
            model_name='booking',
            name='dispositivi_selezionati',
            field=models.ManyToManyField(
                blank=True,
                related_name='prenotazioni',
                to='prenotazioni.device',
            ),
        ),
        migrations.AddField(
            model_name='resource',
            name='dispositivi',
            field=models.ManyToManyField(
                blank=True,
                related_name='risorse',
                to='prenotazioni.device',
                verbose_name='Dispositivi Associati',
            ),
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['user']),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['attivo']),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['verificato']),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['codice_inventario']),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['tipo', 'stato']),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['categoria']),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['attivo']),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['utente', 'inizio']),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['risorsa', 'inizio', 'fine']),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['stato']),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['inizio', 'fine']),
        ),
        
        # Add constraints
        migrations.AddConstraint(
            model_name='booking',
            constraint=models.CheckConstraint(
                check=models.Q(fine__gt=models.F('inizio')),
                name='valid_date_range',
            ),
        ),
        migrations.AddConstraint(
            model_name='booking',
            constraint=models.CheckConstraint(
                check=models.Q(quantita__gt=0),
                name='positive_quantity',
            ),
        ),
    ]
```

#### Step 2: Crea comando migration automatica
Crea file `prenotazioni/management/commands/fix_migration.py`:

```python
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Applica la migrazione completa per sistemare database'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Applicazione migrazione database...")
        
        # Esegui le migrazioni
        from django.core.management import call_command
        call_command('migrate', verbosity=2)
        
        # Crea dati iniziali
        self.stdout.write("📊 Creazione dati iniziali...")
        call_command('create_initial_data', verbosity=1)
        
        self.stdout.write(self.style.SUCCESS("✅ Database sistemato con successo!"))
```

#### Step 3: Push su GitHub e redeploy
1. Salva i file su GitHub
2. Il redeploy automatico creerà le tabelle mancanti

---

### 🎯 OPZIONE 2: Reset Database Neon

#### Step 1: Reset completo database
1. Vai su https://neon.tech
2. Seleziona il database
3. Clicca "Reset Database" 
4. Conferma reset

#### Step 2: Configurazione automatica
Modifica il file di deploy per fare migrate automaticamente:

Crea/modifica `entrypoint.sh`:

```bash
#!/bin/bash
echo "🚀 Setup database e applicazione..."

# Attendi che il database sia pronto
echo "⏳ Attesa connessione database..."
python manage.py migrate --check
python manage.py migrate --settings=config.settings

# Crea dati iniziali
echo "📊 Creazione dati iniziali..."
python manage.py create_initial_data --settings=config.settings

# Avvia applicazione
echo "🎯 Avvio applicazione..."
exec "$@"
```

---

### 🎯 OPZIONE 3: Script SQL Diretto

#### Step 1: Vai su Neon Console
1. Accedi a https://neon.tech
2. Apri il tuo database
3. Vai su "SQL Editor"

#### Step 2: Esegui questo SQL completo
```sql
-- Tabella Configuration
CREATE TABLE "prenotazioni_configuration" (
    "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    "chiave" varchar(100) NOT NULL UNIQUE,
    "valore" text NOT NULL,
    "tipo" varchar(20) NOT NULL,
    "descrizione" text,
    "modificabile" boolean NOT NULL DEFAULT true,
    "creato_il" timestamp WITH TIME ZONE NOT NULL,
    "modificato_il" timestamp WITH TIME ZONE NOT NULL
);

-- Tabella SchoolInfo
CREATE TABLE "prenotazioni_schoolinfo" (
    "id" bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    "nome_completo" varchar(200) NOT NULL,
    "nome_breve" varchar(100) NOT NULL,
    "codice_meccanografico" varchar(10) NOT NULL UNIQUE,
    "partita_iva" varchar(20),
    "sito_web" varchar(200) NOT NULL,
    "email_istituzionale" varchar(254) NOT NULL,
    "telefono" varchar(20),
    "fax" varchar(20),
    "indirizzo" text NOT NULL,
    "cap" varchar(10) NOT NULL,
    "comune" varchar(100) NOT NULL,
    "provincia" varchar(50) NOT NULL,
    "regione" varchar(50) NOT NULL,
    "nazione" varchar(50) NOT NULL DEFAULT 'Italia',
    "latitudine" numeric(10, 8),
    "longitudine" numeric(11, 8),
    "attivo" boolean NOT NULL DEFAULT true,
    "creato_il" timestamp WITH TIME ZONE NOT NULL,
    "modificato_il" timestamp WITH TIME ZONE NOT NULL
);

-- Continua con tutte le altre tabelle...
-- (Il contenuto SQL completo è molto lungo e va adattato per ogni tabella)
```

---

## 🚀 RACCOMANDAZIONE FINALE

**USA OPZIONE 1** (Modifica GitHub + Redeploy) perché:
- ✅ Più sicura
- ✅ Versionata
- ✅ Automatica
- ✅ Senza perdita dati

Procedi con l'Opzione 1 e fammi sapere come va!
