#!/usr/bin/env python
# Update admin_operazioni.html
import sys

file_path = r'prenotazioni/templates/prenotazioni/admin_operazioni.html'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update the reference to use setup_amministratore instead
    old = "{% url 'prenotazioni:configurazione_sistema' %}"
    new = "{% url 'prenotazioni:setup_amministratore' %}"
    content = content.replace(old, new)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✓ Updated admin_operazioni.html')
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
