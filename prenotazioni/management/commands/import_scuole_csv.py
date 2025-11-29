from django.core.management.base import BaseCommand
from django.conf import settings
import os
import csv
import json


class Command(BaseCommand):
    help = 'Importa un CSV di anagrafica scuole e crea un indice JSON per lookup codice meccanografico.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', nargs='?', help='Percorso al file CSV di input (es: backups/scuole_anagrafe.csv)')

    def handle(self, *args, **options):
        csv_path = options.get('csv_path') or os.path.join(settings.BASE_DIR, 'backups', 'scuole_anagrafe.csv')
        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f'File CSV non trovato: {csv_path}'))
            self.stderr.write('Scarica il dataset ufficiale dal portale open-data del Ministero e salvalo come CSV in `backups/scuole_anagrafe.csv` oppure passa il percorso come argomento.')
            return

        out_path = os.path.join(settings.BASE_DIR, 'backups', 'scuole_index.json')
        index = {}
        with open(csv_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            for row in rows:
                # find probable codice field
                codice = None
                for k in row.keys():
                    kl = k.lower()
                    if 'cod' in kl and ('mecc' in kl or 'meccan' in kl or 'istit' in kl or 'scuola' in kl):
                        codice = row[k]
                        break
                if not codice:
                    # try common names
                    for alt in ['codice','codice_meccanografico','cod_istituto','codicescuola','cod_meccanografico']:
                        if alt in row:
                            codice = row[alt]
                            break
                if not codice:
                    continue
                codice_norm = ''.join(str(codice).upper().split())

                def pick(keys):
                    for kk in keys:
                        if kk in row and row[kk]:
                            return row[kk]
                    return ''

                nome = pick(['denominazione','denominazione_istituto','denominazione_scuola','nome','descrizione'])
                indirizzo = pick(['indirizzo','via','indirizzo_scuola','indirizzo_istituto','address'])
                cap = pick(['cap','codice_postale','zip'])
                comune = pick(['comune','municipio','localita','town','city'])
                provincia = pick(['provincia','prov','county'])
                regione = pick(['regione','region'])
                lat = pick(['latitudine','lat','latitude'])
                lon = pick(['longitudine','lon','longitude'])

                index[codice_norm] = {
                    'codice': codice_norm,
                    'nome': nome,
                    'indirizzo': indirizzo,
                    'cap': cap,
                    'comune': comune,
                    'provincia': provincia,
                    'regione': regione,
                    'lat': lat,
                    'lon': lon,
                }

        with open(out_path, 'w', encoding='utf-8') as of:
            json.dump(index, of, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f'Indice creato: {out_path} ({len(index)} voci)'))
