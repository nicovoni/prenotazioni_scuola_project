#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/giorg/siricomincia/prenotazioni_scuola_project')
django.setup()

from prenotazioni.models import UbicazioneRisorsa

count = UbicazioneRisorsa.objects.count()
print(f'Total UbicazioneRisorsa records: {count}')

# Show some samples with codice_meccanografico
samples = UbicazioneRisorsa.objects.filter(
    codice_meccanografico__isnull=False
).exclude(codice_meccanografico__exact='')[:5]

print(f'\nSample records:')
for u in samples:
    print(f'  {u.codice_meccanografico}: {u.nome}')

# Check for GRIS001009
gris = UbicazioneRisorsa.objects.filter(codice_meccanografico='GRIS001009').first()
if gris:
    print(f'\nGRIS001009 found: {gris.nome}')
else:
    print('\nGRIS001009 not found!')
