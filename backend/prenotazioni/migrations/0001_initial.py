# Generated manually for Render deployment

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Utente',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('ruolo', models.CharField(choices=[('docente', 'Docente'), ('studente', 'Studente'), ('assistente', 'Assistente tecnico'), ('admin', 'Amministratore')], default='studente', help_text='Ruolo dell\'utente nel sistema scolastico', max_length=20, verbose_name='Ruolo')),
                ('telefono', models.CharField(blank=True, help_text='Numero di telefono dell\'utente', max_length=20, null=True, verbose_name='Telefono')),
                ('classe', models.CharField(blank=True, help_text='Classe di appartenenza (per studenti)', max_length=10, null=True, verbose_name='Classe')),
            ],
            options={
                'verbose_name': 'Utente',
                'verbose_name_plural': 'Utenti',
            },
        ),
        migrations.CreateModel(
            name='Risorsa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(help_text='Nome identificativo della risorsa', max_length=120, verbose_name='Nome risorsa')),
                ('tipo', models.CharField(choices=[('lab', 'Laboratorio'), ('carrello', 'Carrello')], help_text='Tipo di risorsa (laboratorio o carrello)', max_length=20, verbose_name='Tipo')),
                ('quantita_totale', models.PositiveIntegerField(blank=True, help_text='Numero totale di postazioni/dispositivi disponibili', null=True, verbose_name='Quantità totale')),
            ],
            options={
                'verbose_name': 'Risorsa',
                'verbose_name_plural': 'Risorse',
            },
        ),
        migrations.CreateModel(
            name='Prenotazione',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantita', models.PositiveIntegerField(default=1, help_text='Numero di postazioni/dispositivi richiesti', verbose_name='Quantità')),
                ('inizio', models.DateTimeField(help_text='Inizio del periodo di prenotazione', verbose_name='Data/ora inizio')),
                ('fine', models.DateTimeField(help_text='Fine del periodo di prenotazione', verbose_name='Data/ora fine')),
                ('risorsa', models.ForeignKey(help_text='Risorsa prenotata', on_delete=django.db.models.deletion.CASCADE, to='prenotazioni.risorsa', verbose_name='Risorsa')),
                ('utente', models.ForeignKey(help_text='Utente che ha effettuato la prenotazione', on_delete=django.db.models.deletion.CASCADE, to='prenotazioni.utente', verbose_name='Utente')),
            ],
            options={
                'verbose_name': 'Prenotazione',
                'verbose_name_plural': 'Prenotazioni',
                'ordering': ['-inizio'],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('prenotazioni.utente',),
        ),
        migrations.AddField(
            model_name='utente',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='utente',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
    ]
