"""
Management command to create initial data for the booking system.
"""
from django.core.management.base import BaseCommand
from prenotazioni.models import Risorsa


class Command(BaseCommand):
    help = 'Create initial resources (laboratories and equipment) for the booking system'

    def handle(self, *args, **options):
        self.stdout.write('Creating initial resources...')

        # Create laboratories
        laboratories = [
            {'nome': 'Laboratorio di Informatica 1', 'tipo': 'lab', 'quantita_totale': 24},
            {'nome': 'Laboratorio di Informatica 2', 'tipo': 'lab', 'quantita_totale': 24},
            {'nome': 'Laboratorio di Informatica 3', 'tipo': 'lab', 'quantita_totale': 20},
            {'nome': 'Laboratorio di Scienze', 'tipo': 'lab', 'quantita_totale': 16},
            {'nome': 'Laboratorio di Arte', 'tipo': 'lab', 'quantita_totale': 12},
        ]

        # Create equipment carts
        equipment = [
            {'nome': 'Carrello Notebook', 'tipo': 'carrello', 'quantita_totale': 25},
            {'nome': 'Carrello iPad', 'tipo': 'carrello', 'quantita_totale': 30},
        ]

        created_count = 0

        # Create laboratories
        for lab_data in laboratories:
            risorsa, created = Risorsa.objects.get_or_create(
                nome=lab_data['nome'],
                defaults={
                    'tipo': lab_data['tipo'],
                    'quantita_totale': lab_data['quantita_totale']
                }
            )
            if created:
                self.stdout.write(f'  Created: {risorsa.nome} ({risorsa.quantita_totale} posti)')
                created_count += 1
            else:
                self.stdout.write(f'  Already exists: {risorsa.nome}')

        # Create equipment
        for equip_data in equipment:
            risorsa, created = Risorsa.objects.get_or_create(
                nome=equip_data['nome'],
                defaults={
                    'tipo': equip_data['tipo'],
                    'quantita_totale': equip_data['quantita_totale']
                }
            )
            if created:
                self.stdout.write(f'  Created: {risorsa.nome} ({risorsa.quantita_totale} unità)')
                created_count += 1
            else:
                self.stdout.write(f'  Already exists: {risorsa.nome}')

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} resources')
            )
        else:
            self.stdout.write(
                self.style.WARNING('All resources already exist')
            )
