#!/usr/bin/env python
"""
Script per modificare la funzione lookup_unica() aggiungendo supporto per scuole affiliate.
"""

import os
import sys

# Leggi il file views.py
views_path = r'c:\Users\giorg\siricomincia\prenotazioni_scuola_project\prenotazioni\views.py'

with open(views_path, 'r', encoding='utf-8') as f:
    content = f.read()

# La parte da sostituire è quella alla fine della funzione lookup_unica()
# Troviamo la linea che inizia con "    codice_norm = normalize_codice(codice)"
# e la sostituiamo con la nuova logica

old_ending = '''    codice_norm = normalize_codice(codice)
    data = index.get(codice_norm)
    if not data:
        return JsonResponse({'error': 'not_found', 'message': 'Codice non trovato nell\'indice locale.'}, status=404)

    return JsonResponse({'error': None, 'data': data})'''

new_ending = '''    codice_norm = normalize_codice(codice)
    data = index.get(codice_norm)
    if not data:
        return JsonResponse({'error': 'not_found', 'message': 'Codice non trovato nell\'indice locale.'}, status=404)

    # Logica per scuole affiliate
    # Se questo codice ha sede_direttivo=SI, è una scuola principale
    # Altrimenti, trova la scuola principale attraverso codice_istituto
    
    main_institute = None
    affiliated_schools = []
    
    # Se questo è il codice principale (sede_direttivo=SI)
    if data.get('sede_direttivo', '').upper() == 'SI':
        main_institute = data
        # Trova tutte le scuole affiliate con lo stesso codice_istituto
        if data.get('codice_istituto'):
            for idx_code, idx_data in index.items():
                if idx_data.get('codice_istituto') == data.get('codice_istituto'):
                    if idx_code != codice_norm:  # Escludi la principale stessa
                        affiliated_schools.append(idx_data)
    else:
        # Questo è un codice di una scuola figlia
        # Trova la scuola principale
        if data.get('codice_istituto'):
            for idx_code, idx_data in index.items():
                if idx_data.get('codice_istituto') == data.get('codice_istituto') and idx_data.get('sede_direttivo', '').upper() == 'SI':
                    main_institute = idx_data
                    break
        
        # Se non trovata, usa la scuola corrente come principale
        if main_institute is None:
            main_institute = data
        
        # Trova tutte le scuole affiliate
        if main_institute.get('codice_istituto'):
            for idx_code, idx_data in index.items():
                if idx_data.get('codice_istituto') == main_institute.get('codice_istituto'):
                    if idx_code != main_institute['codice']:  # Escludi la principale
                        affiliated_schools.append(idx_data)
    
    return JsonResponse({
        'error': None, 
        'data': main_institute,
        'affiliated_schools': affiliated_schools
    })'''

if old_ending in content:
    content = content.replace(old_ending, new_ending)
    print("✓ Replacement successful!")
else:
    print("✗ Old ending not found. Trying alternative search...")
    # Prova a trovare la sezione in modo più flessibile
    if "codice_norm = normalize_codice(codice)" in content and "return JsonResponse({'error': None, 'data': data})" in content:
        # Trova l'indice di inizio
        start_idx = content.rfind("    codice_norm = normalize_codice(codice)")
        if start_idx != -1:
            # Trova l'indice di fine (la riga di return)
            end_idx = content.find("return JsonResponse({'error': None, 'data': data})", start_idx)
            if end_idx != -1:
                end_idx = content.find('\n', end_idx) + 1
                # Sostituisci
                old_text = content[start_idx:end_idx]
                new_text = new_ending + '\n'
                content = content[:start_idx] + new_text + content[end_idx:]
                print("✓ Replacement successful with flexible search!")
            else:
                print("✗ Could not find end of section")
                sys.exit(1)
        else:
            print("✗ Could not find start of section")
            sys.exit(1)
    else:
        print("✗ Could not find the section to replace")
        sys.exit(1)

# Scrivi il file modificato
with open(views_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✓ File modified successfully: {views_path}")
print("✓ lookup_unica() now returns affiliated_schools!")
