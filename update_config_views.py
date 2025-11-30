file = 'config/views.py'
with open(file, 'r') as f:
    content = f.read()

# Replace references to configurazione_sistema with setup_amministratore
content = content.replace(
    "return redirect('prenotazioni:configurazione_sistema')",
    "return redirect('prenotazioni:setup_amministratore')"
)

with open(file, 'w') as f:
    f.write(content)

print('✓ Updated config/views.py')
