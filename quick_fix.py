import sys
import os

# Read the original file
view_file = 'prenotazioni/views.py'
with open(view_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the location to replace - cerca la riga che finisce la funzione lookup_unica
# Usa un approccio più robusto: cerca il pattern parziale
old_snippet = "    return JsonResponse({'error': None, 'data': data})\n\n\ndef admin_operazioni"

new_snippet = """    # Logica per scuole affiliate
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
    })


def admin_operazioni"""

if old_snippet in content:
    content = content.replace(old_snippet, new_snippet)
    with open(view_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ SUCCESS: File modified!")
    sys.exit(0)
else:
    # Try even simpler approach
    if "return JsonResponse({'error': None, 'data': data})" in content:
        # Find position
        pos = content.find("return JsonResponse({'error': None, 'data': data})")
        # Get surrounding context
        context_start = max(0, pos - 200)
        context_end = min(len(content), pos + 100)
        print("Context around target:")
        print(repr(content[context_start:context_end]))
        sys.exit(1)
    else:
        print("ERROR: Could not find target string")
        sys.exit(1)
