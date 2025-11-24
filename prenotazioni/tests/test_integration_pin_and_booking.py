from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from prenotazioni.models import Risorsa
from prenotazioni.services import UserSessionService, BookingService


class PinSessionIntegrationTest(TestCase):
    def test_pin_flow_and_verification(self):
        User = get_user_model()
        user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')

        # genera PIN e crea sessione
        pin = UserSessionService.generate_pin()
        session = UserSessionService.create_session(user=user, tipo='login_pin', email_destinazione=user.email, pin=pin)
        self.assertIsNotNone(session)

        # verifica con PIN corretto
        success, message = UserSessionService.verify_session(session.token_sessione, pin=pin)
        self.assertTrue(success, msg=f"Expected pin verification to succeed, got: {message}")

        # verifica con PIN errato
        # crea nuova sessione
        pin2 = UserSessionService.generate_pin()
        session2 = UserSessionService.create_session(user=user, tipo='login_pin', email_destinazione=user.email, pin=pin2)
        self.assertIsNotNone(session2)

        success2, message2 = UserSessionService.verify_session(session2.token_sessione, pin='000000')
        self.assertFalse(success2)


class BookingIntegrationTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='bookuser', email='book@example.com', password='pass')

        # crea risorsa laboratorio
        self.risorsa = Risorsa.objects.create(
            nome='Lab 1',
            codice='LAB1',
            tipo='laboratorio',
            attivo=True
        )

    def test_create_booking_and_conflict(self):
        inizio = timezone.now() + timedelta(days=1)
        fine = inizio + timedelta(hours=2)

        success, result = BookingService.create_booking(
            utente=self.user,
            risorsa_id=self.risorsa.id,
            quantita=1,
            inizio=inizio,
            fine=fine
        )
        self.assertTrue(success, msg=f"Booking creation failed: {result}")
        booking = result if success else None
        self.assertIsNotNone(booking)

        # tentativo di creare una seconda prenotazione nello stesso intervallo (laboratorio esclusivo)
        success2, result2 = BookingService.create_booking(
            utente=self.user,
            risorsa_id=self.risorsa.id,
            quantita=1,
            inizio=inizio + timedelta(minutes=30),
            fine=fine + timedelta(minutes=30)
        )
        self.assertFalse(success2, msg="Expected conflict preventing second booking for laboratorio")
