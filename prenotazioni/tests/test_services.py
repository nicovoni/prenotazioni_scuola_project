from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from prenotazioni.services import BookingService, NotificationService
from prenotazioni.models import (
    Risorsa, StatoPrenotazione, TemplateNotifica, NotificaUtente
)

User = get_user_model()


class BookingAndNotificationServiceTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')

        # Create a resource (laboratorio)
        self.resource = Risorsa.objects.create(
            nome='Lab A',
            codice='LAB-A',
            tipo='laboratorio',
            attivo=True
        )

        # Ensure booking status template exists will be created by service when needed

        # Create notification template for booking_created used by BookingService
        TemplateNotifica.objects.create(
            nome='booking_created',
            tipo='email',
            evento='booking_created',
            oggetto='Conferma Prenotazione - $resource_name',
            contenuto='Ciao $username, la tua prenotazione per $resource_name è stata creata.',
            attivo=True
        )

    def test_create_booking_creates_booking_and_notification(self):
        now = timezone.now()
        start = now + timedelta(hours=1)
        end = now + timedelta(hours=2)

        success, result = BookingService.create_booking(
            utente=self.user,
            risorsa_id=self.resource.id,
            quantita=1,
            inizio=start,
            fine=end
        )

        self.assertTrue(success, f"Booking creation failed: {result}")
        # If booking created, result should be a Prenotazione instance
        booking = result
        self.assertIsNotNone(booking.id)

        # A notification for booking_created should exist for the user
        notifications = NotificaUtente.objects.filter(utente=self.user, tipo='booking_created')
        self.assertTrue(notifications.exists(), "booking_created notification not created")

    def test_create_notification_renders_and_creates(self):
        # Create a generic template
        tmpl = TemplateNotifica.objects.create(
            nome='test_template',
            tipo='email',
            evento='test_event',
            oggetto='Ciao $username',
            contenuto='Messaggio per $username',
            attivo=True
        )

        notif = NotificationService.create_notification(self.user, 'test_template', {'username': self.user.username})
        self.assertIsNotNone(notif)
        self.assertEqual(notif.utente, self.user)
        self.assertIn(self.user.username, notif.titolo)

*** End Patch