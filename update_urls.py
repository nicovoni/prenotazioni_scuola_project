import re

file = "prenotazioni/urls.py"
with open(file, "r") as f:
    content = f.read()

# Remove "configurazione_sistema" from imports
content = re.sub(
    r"from \.views import.*",
    "from .views import BookingViewSet, prenota_laboratorio, lista_prenotazioni, edit_prenotazione, delete_prenotazione, database_viewer, admin_operazioni, setup_amministratore, lookup_unica",
    content,
    count=1
)

# Add redirect import
content = content.replace(
    "from django.urls import path, include",
    "from django.urls import path, include\nfrom django.shortcuts import redirect"
)

# Replace the configurazione_sistema path with redirect - handle single quotes version
old_path1 = "path('configurazione-sistema/', login_required(admin_required(configurazione_sistema)), name='configurazione_sistema'),"
new_path = "path('configurazione-sistema/', lambda request: redirect('prenotazioni:setup_amministratore'), name='configurazione_sistema'),"
content = content.replace(old_path1, new_path)

with open(file, "w") as f:
    f.write(content)

print("✓ Updated urls.py")
