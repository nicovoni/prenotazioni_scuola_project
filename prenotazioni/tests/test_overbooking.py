from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from prenotazioni.services import BookingService
from prenotazioni.models import (
    Risorsa, Prenotazione, TemplateNotifica, NotificaUtente
)

User = get_user_model()


class OverbookingTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser2', email='test2@example.com', password='pass')

        # Create a carrello resource with capacity 5
        self.resource = Risorsa.objects.create(
            nome='Carrello 1',
            codice='CARR-1',
            tipo='carrello',
            attivo=True,
            capacita_massima=5
        )

        # Create notification template to avoid missing-template issues
        TemplateNotifica.objects.create(
            nome='booking_created',
            tipo='email',
            evento='booking_created',
            oggetto='Conferma Prenotazione',
            contenuto='Conferma',
            attivo=True
        )

    def test_overbooking_fails_when_not_enough_capacity(self):
        now = timezone.now()
        start = now + timedelta(hours=1)
        end = now + timedelta(hours=2)

        # Existing booking occupies 4 units
        existing = Prenotazione.objects.create(
            utente=self.user,
            risorsa=self.resource,
            quantita=4,
            inizio=start,
            fine=end
        )

        # Try to create a booking of quantity 2 -> should fail (only 1 left)
        success, result = BookingService.create_booking(
            utente=self.user,
            risorsa_id=self.resource.id,
            quantita=2,
            inizio=start,
            fine=end
        )

        self.assertFalse(success)
        self.assertIn('Disponibilità insufficiente', str(result))

    def test_overbooking_succeeds_when_capacity_sufficient(self):
        now = timezone.now()
        start = now + timedelta(hours=3)
        end = now + timedelta(hours=4)

        # Existing booking occupies 2 units (different time slot)
        existing = Prenotazione.objects.create(
            utente=self.user,
            risorsa=self.resource,
            quantita=2,
            inizio=start - timedelta(days=1),
            fine=end - timedelta(days=1)
        )

        # Create booking now for time slot with full capacity available
        success, booking = BookingService.create_booking(
            utente=self.user,
            risorsa_id=self.resource.id,
            quantita=5,
            inizio=start,
            fine=end
        )

        self.assertTrue(success)
        self.assertIsNotNone(booking.id)
*** End Patch