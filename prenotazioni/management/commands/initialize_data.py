"""
Management command per inizializzare i dati del sistema scolastico alla prima esecuzione.

Questo comando viene eseguito automaticamente durante il deploy su Render,
popolando il database con le informazioni essenziali per il funzionamento.
"""

import os
import logging
from django.core.management.base import BaseCommand
from prenotazioni.models import (
    InformazioniScuola, Risorsa, Dispositivo, ConfigurazioneSistema,
    UbicazioneRisorsa, CategoriaDispositivo, StatoPrenotazione, ProfiloUtente
)
from django.contrib.auth.models import User as DjangoUser
from prenotazioni.services import SystemInitializer

# Dati iniziali da configurare via env vars o hardcoded
DEFAULT_SCHOOL_DATA = {
    'nome_completo_scuola': os.environ.get('SCHOOL_NAME', 'Istituto Statale di Istruzione Superiore di Follonica'),
    'nome_breve_scuola': os.environ.get('SCHOOL_SHORT_NAME', 'ISIUFol'),
    'codice_meccanografico_scuola': os.environ.get('SCHOOL_CODE', 'TSAA82000A'),
    'sito_web_scuola': os.environ.get('SCHOOL_WEBSITE', 'https://www.isufol.it'),
    'email_istituzionale_scuola': os.environ.get('SCHOOL_EMAIL', 'info@isufol.it'),
    'indirizzo_scuola': os.environ.get('SCHOOL_ADDRESS', 'Via Martiri della Libertà, 1 - 58022 Follonica (GR)'),
    'telefono_scuola': os.environ.get('SCHOOL_PHONE', '+39 0566 12345'),
    'provincia_scuola': 'GR',
    'regione_scuola': 'Toscana',
    'nazione_scuola': 'Italia',
}

DEFAULT_RESOURCES = [
    {
        'nome': 'Laboratorio Informatica 1',
        'codice': 'LAB_INF_01',
        'tipo': 'laboratorio',
        'capacita_massima': 24,
        'postazioni_disponibili': 24,
        'orari_apertura': {'8:00': '18:00'},
        'descrizione': 'Laboratorio principale con postazioni Windows',
        'edificio': 'A',
        'piano': 'Piano Terra',
        'aula': 'A01',
    },
    {
        'nome': 'Laboratorio Informatica 2',
        'codice': 'LAB_INF_02',
        'tipo': 'laboratorio',
        'capacita_massima': 24,
        'postazioni_disponibili': 24,
        'orari_apertura': {'8:00': '18:00'},
        'descrizione': 'Laboratorio secondario con postazioni Linux',
        'edificio': 'A',
        'piano': 'Piano Terra',
        'aula': 'A02',
    },
    {
        'nome': 'Carrello iPad',
        'codice': 'CART_IPAD_01',
        'tipo': 'carrello',
        'capacita_massima': int(os.environ.get('CART_IPAD_TOTAL', 25)),
        'orari_apertura': {'8:00': '18:00'},
        'descrizione': 'Carrello con iPad per didattica digitale',
        'edificio': 'A',
        'piano': 'Piano Terra',
        'aula': 'Deposito',
    },
    {
        'nome': 'Carrello Notebook',
        'codice': 'CART_NB_01',
        'tipo': 'carrello',
        'capacita_massima': int(os.environ.get('CART_NOTEBOOK_TOTAL', 30)),
        'orari_apertura': {'8:00': '18:00'},
        'descrizione': 'Carrello con notebook Windows portatili',
        'edificio': 'A',
        'piano': 'Piano Terra',
        'aula': 'Deposito',
    },
    {
        'nome': 'Aula Magna',
        'codice': 'AULA_MAGNA',
        'tipo': 'aula',
        'capacita_massima': 100,
        'orari_apertura': {'8:00': '18:00'},
        'descrizione': 'Aula magna con proiettore e impianto audio',
        'edificio': 'B',
        'piano': 'Piano Terra',
        'aula': 'B01',
    },
]

DEFAULT_DEVICES = [
    # Dispositivi per iPad carrello
    {
        'nome': 'iPad Pro 12.9"',
        'marca': 'Apple',
        'modello': 'iPad Pro',
        'tipo': 'tablet',
        'codice_inventario': f'IPAD{i:04d}',
        'categoria_nome': 'Tablet',
    } for i in range(1, int(os.environ.get('CART_IPAD_TOTAL', 25)) + 1)
] + [
    # Dispositivi per notebook carrello
    {
        'nome': 'Laptop Windows',
        'marca': 'HP',
        'modello': 'Pavilion 15',
        'tipo': 'laptop',
        'codice_inventario': f'NB{i:04d}',
        'categoria_nome': 'Computer',
    } for i in range(1, int(os.environ.get('CART_NOTEBOOK_TOTAL', 30)) + 1)
] + [
    # Dispositivi fissi nei laboratori
    {
        'nome': 'PC Fisso Lab 1',
        'marca': 'Dell',
        'modello': 'OptiPlex 7080',
        'tipo': 'desktop',
        'codice_inventario': f'LAB1_PC{i:02d}',
        'categoria_nome': 'Computer',
        'edificio': 'A',
        'piano': 'Piano Terra',
        'aula': 'A01',
    } for i in range(1, 25)
] + [
    {
        'nome': 'PC Fisso Lab 2',
        'marca': 'Dell',
        'modello': 'OptiPlex 7080',
        'tipo': 'desktop',
        'codice_inventario': f'LAB2_PC{i:02d}',
        'categoria_nome': 'Computer',
        'edificio': 'A',
        'piano': 'Piano Terra',
        'aula': 'A02',
    } for i in range(1, 25)
]

DEFAULT_LOCATIONS = [
    {
        'nome': 'Laboratorio Informatica 1',
        'descrizione': 'Locazione fisica del lab informatica principale',
        'edificio': 'A',
        'piano': 'Piano Terra',
        'aula': 'A01',
        'capacita_persone': 24,
    },
    {
        'nome': 'Laboratorio Informatica 2',
        'descrizione': 'Locazione fisica del lab informatica secondario',
        'edificio': 'A',
        'piano': 'Piano Terra',
        'aula': 'A02',
        'capacita_persone': 24,
    },
    {
        'nome': 'Aula Magna',
        'descrizione': 'Aula magna principale',
        'edificio': 'B',
        'piano': 'Piano Terra',
        'aula': 'B01',
        'capacita_persone': 100,
    },
]

# Crea un utente amministratore di default
DEFAULT_ADMIN = {
    'username': os.environ.get('ADMIN_USERNAME', 'toor'),
    'email': os.environ.get('ADMIN_EMAIL', 'admin@isufol.it'),
    'first_name': os.environ.get('ADMIN_FIRST_NAME', 'Amministratore'),
    'last_name': os.environ.get('ADMIN_LAST_NAME', 'Sistema'),
}

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Inizializza il database con dati di base per il sistema scolastico'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forza reinizializzazione anche se dati esistono',
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(
                self.style.SUCCESS('Inizio inizializzazione dati sistema...')
            )

            # Inizializza componenti di sistema
            success, message = SystemInitializer.initialize_system()
            if not success:
                self.stdout.write(
                    self.style.ERROR(f'Errore inizializzazione sistema: {message}')
                )
                return

            self.stdout.write(
                self.style.SUCCESS(message)
            )

            # Crea dati scuola
            if not InformazioniScuola.objects.exists() or options['force']:
                self._create_school_info()
            else:
                self.stdout.write(
                    self.style.WARNING('Dati scuola già presenti, skip')
                )

            # Crea ubicazioni
            if not UbicazioneRisorsa.objects.exists() or options['force']:
                self._create_locations()
            else:
                self.stdout.write(
                    self.style.WARNING('Ubicazioni già presenti, skip')
                )

            # Crea categorie dispositivi
            if not CategoriaDispositivo.objects.exists() or options['force']:
                self._create_device_categories()
            else:
                self.stdout.write(
                    self.style.WARNING('Categorie dispositivi già presenti, skip')
                )

            # Crea dispositivi
            if not Dispositivo.objects.exists() or options['force']:
                self._create_devices()
            else:
                self.stdout.write(
                    self.style.WARNING('Dispositivi già presenti, skip')
                )

            # Crea risorse
            if not Risorsa.objects.exists() or options['force']:
                self._create_resources()
            else:
                self.stdout.write(
                    self.style.WARNING('Risorse già presenti, skip')
                )

            # Crea utente amministratore
            if not DjangoUser.objects.filter(is_superuser=True).exists() or options['force']:
                self._create_admin_user()
            else:
                self.stdout.write(
                    self.style.WARNING('Utente admin già presente, skip')
                )

            # Verifica e segnala eventuali problemi di configurazione
            self._validate_configuration()

            self.stdout.write(
                self.style.SUCCESS('Inizializzazione dati completata con successo!')
            )

        except Exception as e:
            logger.error(f'Errore inizializzazione dati: {str(e)}')
            self.stdout.write(
                self.style.ERROR(f'Errore: {str(e)}')
            )
            raise

    def _create_school_info(self):
        """Crea informazioni scuola."""
        school, created = InformazioniScuola.objects.get_or_create(
            id=1,
            defaults=DEFAULT_SCHOOL_DATA
        )

        if created:
            self.stdout.write(
                f'Creata scuola: {school.nome_breve_scuola}'
            )
        else:
            self.stdout.write(
                f'Aggiornata scuola: {school.nome_breve_scuola}'
            )

    def _create_locations(self):
        """Crea ubicazioni fisiche."""
        for loc_data in DEFAULT_LOCATIONS:
            loc, created = UbicazioneRisorsa.objects.get_or_create(
                nome=loc_data['nome'],
                defaults=loc_data
            )
            if created:
                self.stdout.write(f'Creata ubicazione: {loc.nome}')

    def _create_device_categories(self):
        """Crea categorie dispositivi."""
        categories = [
            {'nome': 'Computer', 'icona': 'bi-laptop', 'colore': '#007bff', 'ordine': 1},
            {'nome': 'Tablet', 'icona': 'bi-tablet', 'colore': '#28a745', 'ordine': 2},
            {'nome': 'Proiettori', 'icona': 'bi-camera-video', 'colore': '#ffc107', 'ordine': 3},
            {'nome': 'Audio', 'icona': 'bi-speaker', 'colore': '#17a2b8', 'ordine': 4},
            {'nome': 'Altro', 'icona': 'bi-gear', 'colore': '#6c757d', 'ordine': 5},
        ]

        for cat_data in categories:
            cat, created = CategoriaDispositivo.objects.get_or_create(
                nome=cat_data['nome'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Creata categoria: {cat.nome}')

    def _create_devices(self):
        """Crea dispositivi del sistema."""
        created_count = 0

        for device_data in DEFAULT_DEVICES:
            # Ottiene categoria
            categoria = None
            if device_data.get('categoria_nome'):
                try:
                    categoria = CategoriaDispositivo.objects.get(nome=device_data['categoria_nome'])
                except CategoriaDispositivo.DoesNotExist:
                    pass

            device, created = Dispositivo.objects.get_or_create(
                codice_inventario=device_data['codice_inventario'],
                defaults={
                    **device_data,
                    'categoria': categoria,
                }
            )

            if created:
                created_count += 1

        self.stdout.write(
            f'Creati {created_count} dispositivi'
        )

    def _create_resources(self):
        """Crea risorse prenotabili."""
        for res_data in DEFAULT_RESOURCES:
            # Trova ubicazione se specificata
            ubicazione = None
            if res_data.get('edificio') and res_data.get('piano') and res_data.get('aula'):
                try:
                    ubicazione = UbicazioneRisorsa.objects.get(
                        edificio=res_data['edificio'],
                        piano=res_data['piano'],
                        aula=res_data['aula']
                    )
                except UbicazioneRisorsa.DoesNotExist:
                    # Crea ubicazione se non esiste
                    ubicazione = UbicazioneRisorsa.objects.create(
                        nome=f"{res_data['tipo'].title()} {res_data['nome']}",
                        edificio=res_data['edificio'],
                        piano=res_data['piano'],
                        aula=res_data['aula'],
                        descrizione=f"Ubicazione per {res_data['nome']}"
                    )

            # Rimuovi campi di ubicazione dai dati risorsa
            resource_fields = {k: v for k, v in res_data.items()
                             if k not in ['edificio', 'piano', 'aula']}

            resource, created = Risorsa.objects.get_or_create(
                codice=res_data['codice'],
                defaults={
                    **resource_fields,
                    'localizzazione': ubicazione,
                }
            )

            if created:
                self.stdout.write(f'Creata risorsa: {resource.nome}')

                # Associa dispositivi alla risorsa se necessario
                self._associate_devices_to_resource(resource)

    def _associate_devices_to_resource(self, resource):
        """Associa dispositivi alle risorse (laboratori e carrelli)."""

        # Per carrelli
        if resource.tipo == 'carrello' and 'iPad' in resource.nome:
            devices = Dispositivo.objects.filter(
                tipo='tablet',
                categoria__nome='Tablet'
            )
            resource.dispositivi.add(*devices)
            self.stdout.write(f'Associati {devices.count()} iPad al carrello')

        elif resource.tipo == 'carrello' and 'Notebook' in resource.nome:
            devices = Dispositivo.objects.filter(
                tipo='laptop',
                categoria__nome='Computer'
            )
            resource.dispositivi.add(*devices)
            self.stdout.write(f'Associati {devices.count()} notebook al carrello')

        # Per laboratori
        elif resource.tipo == 'laboratorio':
            # Trova dispositivi nella stessa ubicazione
            devices = Dispositivo.objects.filter(
                edificio=resource.localizzazione.edificio,
                piano=resource.localizzazione.piano,
                aula=resource.localizzazione.aula
            )
            resource.dispositivi.add(*devices)
            self.stdout.write(f'Associati {devices.count()} dispositivi al laboratorio')

    def _create_admin_user(self):
        """Crea utente amministratore."""
        user, created = DjangoUser.objects.get_or_create(
            username=DEFAULT_ADMIN['username'],
            defaults={
                'email': DEFAULT_ADMIN['email'],
                'first_name': DEFAULT_ADMIN['first_name'],
                'last_name': DEFAULT_ADMIN['last_name'],
                'is_staff': True,
                'is_superuser': True,
            }
        )

        if created:
            # default password for initial boot (must be changed immediately)
            user.set_password(os.environ.get('ADMIN_PASSWORD', 'torero'))
            user.save()

            # Crea profilo utente
            ProfiloUtente.objects.create(
                utente=user,
                nome_utente=DEFAULT_ADMIN['first_name'],
                cognome_utente=DEFAULT_ADMIN['last_name'],
            )

            # mark that this default admin must change password on first login
            try:
                profil = user.profilo_utente
                profil.must_change_password = True
                profil.password_last_changed = None
                profil.save()
            except Exception:
                # If profil not available, ignore; init code may run later
                pass

            self.stdout.write(
                self.style.SUCCESS(f'Utente admin creato: {user.username}')
            )
        else:
            self.stdout.write(
                f'Utente admin esistente: {user.username}'
            )

    def _validate_configuration(self):
        """Valida configurazione di base."""
        issues = []

        # Verifica scuola
        if not InformazioniScuola.objects.exists():
            issues.append('Nessuna informazione scuola configurata')

        # Verifica risorse
        if not Risorsa.objects.filter(attivo=True).exists():
            issues.append('Nessuna risorsa attiva disponibile')

        # Verifica dispositivi
        if not Dispositivo.objects.filter(attivo=True).exists():
            issues.append('Nessun dispositivo attivo disponibile')

        # Verifica stati prenotazione
        if not StatoPrenotazione.objects.exists():
            issues.append('Nessuno stato prenotazione configurato')

        # Verifica configurazioni di sistema
        required_configs = ['BOOKING_START_HOUR', 'BOOKING_END_HOUR']
        for config_key in required_configs:
            if not ConfigurazioneSistema.objects.filter(chiave_configurazione=config_key).exists():
                issues.append(f'Configurazione richiesta mancante: {config_key}')

        if issues:
            self.stdout.write(
                self.style.WARNING('Problemi di configurazione rilevati:')
            )
            for issue in issues:
                self.stdout.write(f'  - {issue}')
        else:
            self.stdout.write(
                self.style.SUCCESS('Configurazione valida')
            )
