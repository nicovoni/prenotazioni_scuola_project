from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import os


class Command(BaseCommand):
    help = 'Sistemi completamente il database e inizializza i dati di base'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔧 SISTEMAZIONE DATABASE SISTEMA PRENOTAZIONI"))
        self.stdout.write("=" * 60)
        
        self.stdout.write("🚀 Step 1: Applicazione migrazioni...")
        self.apply_migrations()
        
        self.stdout.write("📊 Step 2: Creazione dati iniziali...")
        self.create_initial_data()
        
        self.stdout.write("✅ Step 3: Verifica stato database...")
        self.verify_database()
        
        self.stdout.write(self.style.SUCCESS("🎉 DATABASE SISTEMATO CON SUCCESSO!"))

    def apply_migrations(self):
        """Applica tutte le migrazioni"""
        try:
            call_command('migrate', verbosity=1)
            self.stdout.write(self.style.SUCCESS("✅ Migrazioni applicate con successo"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Errore: {e}"))

    def create_initial_data(self):
        """Crea i dati iniziali di base"""
        try:
            from prenotazioni.models import Configuration, SchoolInfo, DeviceCategory
            
            # Configurazioni di base
            configs = [
                {'chiave': 'EMAIL_HOST', 'valore': 'smtp-relay.brevo.com', 'tipo': 'email'},
                {'chiave': 'BOOKING_START_HOUR', 'valore': '08:00', 'tipo': 'booking'},
                {'chiave': 'BOOKING_END_HOUR', 'valore': '18:00', 'tipo': 'booking'},
            ]
            
            for config in configs:
                Configuration.objects.get_or_create(chiave=config['chiave'], defaults=config)
            
            # Informazioni scuola
            SchoolInfo.objects.get_or_create(
                id=1,
                defaults={
                    'nome_completo': 'Istituto Statale di Istruzione Superiore di Follonica',
                    'nome_breve': 'ISIS Follonica',
                    'codice_meccanografico': 'GRIS00700X',
                    'email_istituzionale': 'info@isufol.it',
                }
            )
            
            # Categorie dispositivi
            categories = [
                {'nome': 'Computer', 'descrizione': 'Computer fissi e portatili'},
                {'nome': 'Tablet', 'descrizione': 'Tablet e dispositivi touchscreen'},
            ]
            
            for cat in categories:
                DeviceCategory.objects.get_or_create(nome=cat['nome'], defaults=cat)
            
            self.stdout.write(self.style.SUCCESS("✅ Dati iniziali creati"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Errore: {e}"))

    def verify_database(self):
        """Verifica lo stato del database"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            from prenotazioni.models import Configuration
            count = Configuration.objects.count()
            
            self.stdout.write(f"✅ Database funzionante - Configurazioni: {count}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Errore: {e}"))
