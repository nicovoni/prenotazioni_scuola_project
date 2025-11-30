file = 'prenotazioni/templates/prenotazioni/admin_operazioni.html'
with open(file, 'r') as f:
    content = f.read()

# Update the reference to use setup_amministratore instead
content = content.replace(
    "{% url 'prenotazioni:configurazione_sistema' %}",
    "{% url 'prenotazioni:setup_amministratore' %}"
)

with open(file, 'w') as f:
    f.write(content)

print('✓ Updated admin_operazioni.html')
