#!/usr/bin/env python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DJANGO_DEBUG'] = 'True'

try:
    import django
    django.setup()
    print("✓ Django setup successful")

    # Test the imports that were failing
    from prenotazioni.serializers import BookingWithDetailsSerializer, PrenotazioneSerializer
    print("✓ Serializers import successful")

    from prenotazioni.views import BookingViewSet
    print("✓ Views import successful")

    print("\n🎉 SUCCESS: All imports working! The NameError has been fixed.")

except ImportError as e:
    print(f"✗ Import error: {e}")
except NameError as e:
    print(f"✗ NameError: {e}")
except Exception as e:
    print(f"✗ Other error: {e}")
