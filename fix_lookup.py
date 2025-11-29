#!/usr/bin/env python
# Script per aggiornare la funzione lookup_unica

with open('prenotazioni/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the lookup_unica ending
old_code = """    codice_norm = normalize_codice(codice)
    data = index.get(codice_norm)
    if not data:
        return JsonResponse({'error': 'not_found', 'message': 'Codice non trovato nell'indice locale.'}, status=404)

    return JsonResponse({'error': None, 'data': data})"""

new_code = """    codice_norm = normalize_codice(codice)
    
    # First, find the main institute (istituto principale)
    main_institute = None
    affiliated_schools = []
    istituto_ref = None
    
    # Check if the code itself is an institute (sede_direttivo = SI)
    data_entry = index.get(codice_norm)
    if data_entry and data_entry.get('sede_direttivo', '').upper() == 'SI':
        # This code IS the main institute
        main_institute = data_entry
        istituto_ref = codice_norm
    elif data_entry and data_entry.get('codice_istituto'):
        # This code is a school, find its main institute
        istituto_ref = normalize_codice(data_entry['codice_istituto'])
        main_institute = index.get(istituto_ref)
    else:
        # Try to find in the index by looking for entries with sede_direttivo = SI
        for k, v in index.items():
            if normalize_codice(v.get('codice_istituto', '')) == codice_norm and v.get('sede_direttivo', '').upper() == 'SI':
                main_institute = v
                istituto_ref = k
                break
    
    if not main_institute:
        return JsonResponse({'error': 'not_found', 'message': 'Codice non trovato nell\'indice locale.'}, status=404)
    
    if not istituto_ref:
        istituto_ref = main_institute.get('codice', codice_norm)
        istituto_ref = normalize_codice(istituto_ref)
    
    # Now find all schools affiliated to this institute
    for k, v in index.items():
        if k != istituto_ref and normalize_codice(v.get('codice_istituto', '')) == istituto_ref:
            affiliated_schools.append({
                'codice': v.get('codice'),
                'nome': v.get('nome'),
                'indirizzo': v.get('indirizzo'),
                'cap': v.get('cap'),
                'comune': v.get('comune'),
            })

    return JsonResponse({
        'error': None,
        'data': main_institute,
        'affiliated_schools': affiliated_schools
    })"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('prenotazioni/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Sostituito con successo!")
else:
    print("❌ Codice non trovato")
