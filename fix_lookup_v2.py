#!/usr/bin/env python3
"""Fix lookup_unica with affiliated schools support"""

import os

views_path = r'c:\Users\giorg\siricomincia\prenotazioni_scuola_project\prenotazioni\views.py'

# Read file in binary to preserve exact encoding
with open(views_path, 'rb') as f:
    content = f.read()

# Converti in string
content_str = content.decode('utf-8')

# Find the exact pattern - usa la stringa con l'apostrofo Unicode se presente
patterns_to_find = [
    # Prima prova con apostrofo singolo standard
    "    codice_norm = normalize_codice(codice)\n    data = index.get(codice_norm)\n    if not data:\n        return JsonResponse({'error': 'not_found', 'message': 'Codice non trovato nell'indice locale.'}, status=404)\n\n    return JsonResponse({'error': None, 'data': data})",
    # Prova con vari apostrofi
    "    codice_norm = normalize_codice(codice)\n    data = index.get(codice_norm)\n    if not data:\n        return JsonResponse({'error': 'not_found', 'message': 'Codice non trovato nell\\u2019indice locale.'}, status=404)\n\n    return JsonResponse({'error': None, 'data': data})",
]

replacement_text = """    codice_norm = normalize_codice(codice)
    data = index.get(codice_norm)
    if not data:
        return JsonResponse({'error': 'not_found', 'message': 'Codice non trovato nell'indice locale.'}, status=404)

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
    })"""

found = False
for pattern in patterns_to_find:
    if pattern in content_str:
        print(f"Found pattern!")
        content_str = content_str.replace(pattern, replacement_text)
        found = True
        break

if not found:
    print("Pattern not found with standard patterns. Trying to find just the final return...")
    # Fallback: cerca solo la linea finale
    if "    return JsonResponse({'error': None, 'data': data})" in content_str:
        # Prendi tutto prima di questa linea  nel contesto della funzione
        lines = content_str.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            if line == "    return JsonResponse({'error': None, 'data': data})":
                # Verifica che la linea precedente sia quella attesa
                if i > 0 and "if not data:" in lines[i-1]:
                    # Sostituisci da qui in poi
                    # Ricostruisci dalle linee prima
                    insert_idx = i
                    # Risali fino a "codice_norm = normalize_codice"
                    start_idx = None
                    for j in range(i, -1, -1):
                        if "codice_norm = normalize_codice(codice)" in lines[j]:
                            start_idx = j
                            break
                    
                    if start_idx is not None:
                        # Raccogli le nuove linee
                        new_content_lines = replacement_text.split('\n')
                        # Riconstruisci
                        new_lines = lines[:start_idx] + new_content_lines + lines[i+1:]
                        content_str = '\n'.join(new_lines)
                        found = True
                        print("Found and replaced using fallback method!")
                        break
            new_lines.append(line)

if found:
    # Scrivi il file
    with open(views_path, 'w', encoding='utf-8') as f:
        f.write(content_str)
    print("SUCCESS: File modified successfully!")
    print("lookup_unica() now returns affiliated_schools!")
else:
    print("ERROR: Could not find the pattern to replace")
    # Debug: stampa le ultime righe della funzione
    lines = content_str.split('\n')
    for i, line in enumerate(lines):
        if 'def lookup_unica' in line:
            print(f"\nFound lookup_unica at line {i}")
            # Stampa le ultime 30 righe della funzione
            for j in range(max(i, len(lines)-40), min(i+100, len(lines))):
                print(f"{j}: {repr(lines[j])}")
            break
