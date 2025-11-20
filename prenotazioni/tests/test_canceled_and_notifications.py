from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from prenotazioni.services import BookingService, NotificationService
from prenotazioni.models import (
    Risorsa, Prenotazione, NotificaUtente
)

User = get_user_model()


class CanceledBookingAndNotificationChannelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u3', email='u3@example.com', password='pass')
        self.resource = Risorsa.objects.create(
            nome='Carrello 2',
            codice='CARR-2',
            tipo='carrello',
            attivo=True,
            capacita_massima=3
        )

    def test_booking_ignores_canceled_reservations(self):
        now = timezone.now()
        start = now + timedelta(hours=1)
        end = now + timedelta(hours=2)

        # Create an existing booking then cancel it
        existing = Prenotazione.objects.create(
            utente=self.user,
            risorsa=self.resource,
            quantita=3,
            inizio=start,
            fine=end
        )
        # Mark canceled
        existing.cancellato_il = timezone.now()
        existing.save()

        # Now try to create a booking of full capacity - should succeed because existing is canceled
        success, booking = BookingService.create_booking(
            utente=self.user,
            risorsa_id=self.resource.id,
            quantita=3,
            inizio=start,
            fine=end
        )

        self.assertTrue(success)
        self.assertIsNotNone(booking.id)

    def test_send_pending_notification_non_email_channel_marks_sent(self):
        # Create a pending notification with sms channel
        notif = NotificaUtente.objects.create(
            utente=self.user,
            tipo='reminder_sms',
            canale='sms',
            titolo='Test SMS',
            messaggio='Testo SMS',
            stato='pending',
            prossimo_tentativo=timezone.now() - timedelta(minutes=1)
        )

        # Call send_pending_notifications which should mark sms as sent without external call
        NotificationService.send_pending_notifications()

        notif.refresh_from_db()
        self.assertEqual(notif.stato, 'sent')
        self.assertIsNotNone(notif.inviata_il)
*** End Patch