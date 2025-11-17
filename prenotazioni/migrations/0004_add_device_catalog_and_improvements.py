# Generated migration for Device catalog and resource improvements

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0003_create_school_info'),
    ]

    operations = [
        # 1. Crea tabella Device completa
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome dispositivo')),
                ('tipo', models.CharField(
                    choices=[
                        ('notebook', 'Notebook/Portatile'),
                        ('tablet', 'Tablet'),
                        ('chromebook', 'Chromebook'),
                        ('altro', 'Altro')
                    ],
                    max_length=20,
                    verbose_name='Tipo dispositivo'
                )),
                ('produttore', models.CharField(
                    choices=[
                        ('apple', 'Apple'),
                        ('microsoft', 'Microsoft'),
                        ('google', 'Google'),
                        ('acer', 'Acer'),
                        ('asus', 'Asus'),
                        ('dell', 'Dell'),
                        ('hp', 'HP'),
                        ('lenovo', 'Lenovo'),
                        ('samsung', 'Samsung'),
                        ('altro', 'Altro')
                    ],
                    max_length=20,
                    verbose_name='Produttore'
                )),
                ('modello', models.CharField(blank=True, max_length=100, verbose_name='Modello')),
                ('sistema_operativo', models.CharField(
                    choices=[
                        ('ios', 'iOS/iPadOS'),
                        ('macos', 'macOS'),
                        ('windows', 'Windows'),
                        ('chromeos', 'ChromeOS'),
                        ('linux', 'Linux'),
                        ('android', 'Android'),
                        ('altro', 'Altro')
                    ],
                    max_length=20,
                    verbose_name='Sistema operativo'
                )),
                ('tipo_display', models.CharField(
                    choices=[
                        ('mobile', 'Mobile/Tablet'),
                        ('desktop', 'Desktop/Notebook')
                    ],
                    max_length=10,
                    verbose_name='Tipo display'
                )),
                ('processore', models.CharField(blank=True, max_length=100, verbose_name='Processore')),
                ('storage', models.CharField(blank=True, max_length=50, verbose_name='Storage')),
                ('schermo', models.CharField(blank=True, max_length=50, verbose_name='Schermo')),
                ('caratteristiche_extra', models.TextField(blank=True, verbose_name='Caratteristiche aggiuntive')),
                ('attivo', models.BooleanField(default=True, verbose_name='Attivo')),
            ],
            options={
                'verbose_name': 'Dispositivo',
                'verbose_name_plural': 'Dispositivi',
                'ordering': ['produttore', 'nome'],
            },
        ),

        # 2. Rinomina campo quantita_totale -> capacita_massima in Risorsa
        migrations.RenameField(
            model_name='risorsa',
            old_name='quantita_totale',
            new_name='capacita_massima',
        ),

        # 3. Aggiungi campi alla tabella Risorsa
        migrations.AddField(
            model_name='risorsa',
            name='descrizione',
            field=models.TextField(blank=True, verbose_name='Descrizione'),
        ),
        migrations.AddField(
            model_name='risorsa',
            name='attiva',
            field=models.BooleanField(default=True, verbose_name='Attiva'),
        ),

        # 4. Aggiungi campi alla tabella Prenotazione
        migrations.AddField(
            model_name='prenotazione',
            name='attiva',
            field=models.BooleanField(default=True, verbose_name='Attiva'),
        ),
        migrations.AddField(
            model_name='prenotazione',
            name='creato_il',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Creato il'),
        ),
        migrations.AddField(
            model_name='prenotazione',
            name='modificato_il',
            field=models.DateTimeField(auto_now=True, verbose_name='Modificato il'),
        ),

        # 5. Crea relazione Many-to-Many tra Risorsa e Device
        migrations.AddField(
            model_name='risorsa',
            name='dispositivi',
            field=models.ManyToManyField(
                blank=True,
                related_name='risorse',
                to='prenotazioni.Device',
                verbose_name='Dispositivi disponibili'
            ),
        ),

        # 6. Aggiungi indici per performance
        migrations.AddIndex(
            model_name='risorsa',
            index=models.Index(fields=['tipo', 'attiva'], name='idx_risorsa_tipo_attiva'),
        ),
        migrations.AddIndex(
            model_name='risorsa',
            index=models.Index(fields=['nome'], name='idx_risorsa_nome'),
        ),
        migrations.AddIndex(
            model_name='prenotazione',
            index=models.Index(fields=['inizio', 'fine'], name='idx_prenotazione_range'),
        ),
        migrations.AddIndex(
            model_name='prenotazione',
            index=models.Index(fields=['risorsa', 'inizio', 'fine'], name='idx_prenotazione_risorsa_range'),
        ),
        migrations.AddIndex(
            model_name='prenotazione',
            index=models.Index(fields=['-inizio'], name='idx_prenotazione_inizio_desc'),
        ),
        migrations.AddIndex(
            model_name='prenotazione',
            index=models.Index(fields=['attiva'], name='idx_prenotazione_attiva'),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['produttore', 'nome'], name='idx_device_produttore_nome'),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['attivo'], name='idx_device_attivo'),
        ),

        # 7. Aggiungi constraint per integrità dati
        migrations.AddConstraint(
            model_name='prenotazione',
            constraint=models.CheckConstraint(
                check=models.Q(fine__gt=models.F('inizio')),
                name='chk_fine_dopo_inizio'
            ),
        ),
        migrations.AddConstraint(
            model_name='device',
            constraint=models.UniqueConstraint(
                fields=['nome', 'modello'],
                name='unique_device_nome_modello'
            ),
        ),
    ]
