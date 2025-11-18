# Migration to create initial resources and devices
from django.db import migrations


def create_initial_data(apps, schema_editor):
    """Create initial resources and devices."""
    Device = apps.get_model('prenotazioni', 'Device')
    Risorsa = apps.get_model('prenotazioni', 'Risorsa')
    SchoolInfo = apps.get_model('prenotazioni', 'SchoolInfo')

    # Create school info (singleton pattern - id=1 if not exists)
    SchoolInfo.objects.get_or_create(
        id=1,
        defaults={
            'nome': 'Istituto Statale di Istruzione Superiore di Follonica',
            'codice_meccanografico': 'PIIS012345',
            'sito_web': 'http://www.isufol.it',
            'indirizzo': 'Via dell\'Istruzione, 1 - Follonica (GR) - 58022'
        }
    )

    # Create initial devices
    devices_data = [
        {'nome': 'iPad Pro 12.9"', 'tipo': 'tablet', 'produttore': 'Apple', 'modello': '12.9"', 'attivo': True},
        {'nome': 'iPad Air', 'tipo': 'tablet', 'produttore': 'Apple', 'modello': '10.9"', 'attivo': True},
        {'nome': 'Latitude 5420', 'tipo': 'notebook', 'produttore': 'Dell', 'modello': '5420', 'attivo': True},
        {'nome': 'Latitude 7420', 'tipo': 'notebook', 'produttore': 'Dell', 'modello': '7420', 'attivo': True},
        {'nome': 'Chromebook 3150', 'tipo': 'chromebook', 'produttore': 'Acer', 'modello': '3150', 'attivo': True},
        {'nome': 'ThinkPad T14', 'tipo': 'notebook', 'produttore': 'Lenovo', 'modello': 'T14', 'attivo': True},
    ]

    devices_created = []
    for device_data in devices_data:
        device, created = Device.objects.get_or_create(
            nome=device_data['nome'],
            produttore=device_data['produttore'],
            defaults=device_data
        )
        devices_created.append(device)

    # Create initial resources
    resources_data = [
        # Laboratories (esclusive access)
        {'nome': 'Lab Informatica 1', 'tipo': 'lab', 'capacita_massima': None, 'descrizione': 'Laboratorio principale di informatica', 'attiva': True},
        {'nome': 'Lab Informatica 2', 'tipo': 'lab', 'capacita_massima': None, 'descrizione': 'Laboratorio secondario di informatica', 'attiva': True},
        {'nome': 'Lab Informatica 3', 'tipo': 'lab', 'capacita_massima': None, 'descrizione': 'Laboratorio ausiliario di informatica', 'attiva': True},
        {'nome': 'Lab Informatica 4', 'tipo': 'lab', 'capacita_massima': None, 'descrizione': 'Laboratorio multimediale', 'attiva': True},
        {'nome': 'Lab Informatica 5', 'tipo': 'lab', 'capacita_massima': None, 'descrizione': 'Laboratorio CAD/CAM', 'attiva': True},

        # Carrelli con dispositivi
        {'nome': 'Carrello Tablet', 'tipo': 'carrello', 'capacita_massima': 25, 'descrizione': 'Carrello con tablet per classi', 'attiva': True},
        {'nome': 'Carrello Notebook', 'tipo': 'carrello', 'capacita_massima': 30, 'descrizione': 'Carrello con notebook per studenti', 'attiva': True},
    ]

    for resource_data in resources_data:
        resource, created = Risorsa.objects.get_or_create(
            nome=resource_data['nome'],
            defaults=resource_data
        )

        # Associate devices with carrelli
        if resource.tipo == 'carrello':
            if 'Tablet' in resource.nome:
                # Carrello tablet: solo dispositivi tablet
                tablet_devices = Device.objects.filter(tipo='tablet', attivo=True)
                resource.dispositivi.set(tablet_devices)
            elif 'Notebook' in resource.nome:
                # Carrello notebook: notebook e chromebook
                notebook_devices = Device.objects.filter(tipo__in=['notebook', 'chromebook'], attivo=True)
                resource.dispositivi.set(notebook_devices)


def reverse_initial_data(apps, schema_editor):
    """Reverse migration - remove initial data."""
    Device = apps.get_model('prenotazioni', 'Device')
    Risorsa = apps.get_model('prenotazioni', 'Risorsa')
    SchoolInfo = apps.get_model('prenotazioni', 'SchoolInfo')

    # Remove devices and resources created in this migration
    Device.objects.filter(produttore__in=['Apple', 'Dell', 'Acer', 'Lenovo']).delete()
    Risorsa.objects.filter(tipo__in=['lab', 'carrello']).delete()

    # Remove school info - but be careful not to delete if it has custom data
    # We'll leave school info as is since it might contain real data

class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_initial_data),
    ]
