"""
Management command to create initial data for the booking system.
Or reset all data with --reset option.
"""
from django.core.management.base import BaseCommand
from prenotazioni.models import Prenotazione, Risorsa, Utente


class Command(BaseCommand):
    help = 'Create initial resources (laboratories and equipment) for the booking system. Use --reset to reinitialize all tables.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing data from all tables before creating initial data',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Reinitializing ALL database tables...')
            self.reset_all_data()
        else:
            self.stdout.write('Reinitializing resources...')

        # Clear all existing resources first to ensure we have exactly the required ones
        deleted_count = Risorsa.objects.all().delete()[0]
        if not options['reset']:
            if deleted_count > 0:
                self.stdout.write(f'  Deleted {deleted_count} existing resources')

        # Create laboratory (fixed workstations - cannot be partially booked)
        laboratories = [
            {'nome': 'Laboratorio Multimediale', 'tipo': 'lab', 'quantita_totale': 1},  # 1 means the whole lab
        ]

        # Create equipment carts (can be partially booked)
        equipment = [
            {'nome': 'Carrello iPad', 'tipo': 'carrello', 'quantita_totale': 25},
            {'nome': 'Carrello Notebook', 'tipo': 'carrello', 'quantita_totale': 30},
        ]

        created_count = 0

        # Create laboratories
        for lab_data in laboratories:
            risorsa = Risorsa.objects.create(
                nome=lab_data['nome'],
                tipo=lab_data['tipo'],
                quantita_totale=lab_data['quantita_totale']
            )
            self.stdout.write(f'  Created: {risorsa.nome} ({risorsa.quantita_totale} posti)')
            created_count += 1

        # Create equipment
        for equip_data in equipment:
            risorsa = Risorsa.objects.create(
                nome=equip_data['nome'],
                tipo=equip_data['tipo'],
                quantita_totale=equip_data['quantita_totale']
            )
            self.stdout.write(f'  Created: {risorsa.nome} ({risorsa.quantita_totale} unità)')
            created_count += 1

        if options['reset']:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully reinitialized all database tables and created {created_count} resources')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully reinitialized {created_count} resources')
            )

    def reset_all_data(self):
        """Delete all data from all tables"""
        deleted_prenotazioni = Prenotazione.objects.all().delete()[0]
        deleted_risorse = Risorsa.objects.all().delete()[0]
        deleted_utenti = Utente.objects.all().delete()[0]

        self.stdout.write(f'  Deleted {deleted_prenotazioni} prenotazioni')
        self.stdout.write(f'  Deleted {deleted_risorse} risorse')
        self.stdout.write(f'  Deleted {deleted_utenti} utenti')
