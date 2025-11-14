# Migration to create initial resources automatically

from django.db import migrations


def create_resources(apps, schema_editor):
    # Get the Risorsa model using apps for historical model compatibility
    Risorsa = apps.get_model('prenotazioni', 'Risorsa')

    # Create the three main resources
    resources_data = [
        {'nome': 'Laboratorio Multimediale', 'tipo': 'lab', 'quantita_totale': 1},
        {'nome': 'Carrello iPad', 'tipo': 'carrello', 'quantita_totale': 25},
        {'nome': 'Carrello Notebook', 'tipo': 'carrello', 'quantita_totale': 30},
    ]

    for resource_data in resources_data:
        Risorsa.objects.get_or_create(
            nome=resource_data['nome'],
            defaults={
                'tipo': resource_data['tipo'],
                'quantita_totale': resource_data['quantita_totale']
            }
        )


def remove_resources(apps, schema_editor):
    # Reverse operation: remove the resources
    Risorsa = apps.get_model('prenotazioni', 'Risorsa')
    Risorsa.objects.filter(
        nome__in=['Laboratorio Multimediale', 'Carrello iPad', 'Carrello Notebook']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_resources, reverse_code=remove_resources),
    ]
