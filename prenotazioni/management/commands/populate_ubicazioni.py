import csv
from django.core.management.base import BaseCommand
from prenotazioni.models import UbicazioneRisorsa


class Command(BaseCommand):
    help = 'Popola UbicazioneRisorsa con i dati dei plessi da scuole_anagrafe.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe fatto senza apportare modifiche',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        csv_path = 'backups/scuole_anagrafe.csv'
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'File {csv_path} non trovato')
            )
            return

        self.stdout.write(f'Caricato CSV con {len(rows)} righe')

        # Processa i dati: deduplicati per CODICESCUOLA per ottenere plessi unici
        seen_codes = set()
        unique_scuole = {}
        
        for row in rows:
            codice = row['CODICESCUOLA'].strip()
            if codice and codice not in seen_codes:
                seen_codes.add(codice)
                unique_scuole[codice] = row

        self.stdout.write(f'Trovati {len(unique_scuole)} plessi unici nel CSV')

        updates_count = 0
        created_count = 0

        for codice, data in unique_scuole.items():
            nome = data.get('DENOMINAZIONESCUOLA', '').strip()[:100]
            comune = data.get('DESCRIZIONECOMUNE', '').strip()
            provincia = data.get('PROVINCIA', '').strip()
            indirizzo = data.get('INDIRIZZOSCUOLA', '').strip()

            # Prova a trovare record esistente per codice
            ubicazione = UbicazioneRisorsa.objects.filter(
                codice_meccanografico=codice
            ).first()

            if ubicazione:
                # Aggiorna solo se nome è diverso
                if ubicazione.nome != nome:
                    ubicazione.nome = nome
                    if not dry_run:
                        ubicazione.save()
                    updates_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Aggiornato: {codice} - {nome}')
                    )
            else:
                # Crea nuovo record con i campi obbligatori
                if not dry_run:
                    try:
                        UbicazioneRisorsa.objects.create(
                            nome=nome,
                            codice_meccanografico=codice,
                            edificio=comune or 'Sede',
                            piano='1',
                            aula=nome[:50] if nome else 'Aula',
                        )
                        created_count += 1
                        if created_count % 500 == 0:
                            self.stdout.write(f'  Creati {created_count}...')
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Errore per {codice}: {e}')
                        )
                else:
                    created_count += 1

        mode = 'DRY RUN' if dry_run else 'ESEGUITO'
        self.stdout.write(self.style.SUCCESS(f'\n{mode}:'))
        self.stdout.write(f'  Creati: {created_count}')
        self.stdout.write(f'  Aggiornati: {updates_count}')
        self.stdout.write(f'  Total in DB: {UbicazioneRisorsa.objects.count()}')
