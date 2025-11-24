from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core import mail

from prenotazioni.models import TemplateNotifica, NotificaUtente, Risorsa, Prenotazione, StatoPrenotazione
from prenotazioni.services import NotificationService, BookingService


class NotificationEmailTest(TestCase):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_notification_email_updates_status(self):
        User = get_user_model()
        user = User.objects.create_user(username='notuser', email='notify@example.com', password='pass')

        template = TemplateNotifica.objects.create(
            nome='test_email_template',
            tipo='email',
            evento='test_event',
            oggetto='Oggetto Test',
            contenuto='Ciao {{ user.username }}, questo è un test',
            attivo=True
        )

        notification = NotificaUtente.objects.create(
            utente=user,
            template=template,
            tipo=template.evento,
            canale=template.tipo,
            titolo='Titolo test',
            messaggio='Messaggio test',
            stato='pending'
        )

        # Send using internal helper
        NotificationService._send_notification(notification)

        notification.refresh_from_db()
        self.assertEqual(notification.stato, 'sent')
        self.assertIsNotNone(notification.inviata_il)
        # Email should be in outbox
        self.assertEqual(len(mail.outbox), 1)


class OverbookingCartTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='cartuser', email='cart@example.com', password='pass')
        self.risorsa = Risorsa.objects.create(
            nome='Carrello Test',
            codice='CART01',
            tipo='carrello',
            attivo=True,
            capacita_massima=5,
            allow_overbooking=False,
        )
        # create initial booking occupying 3 units
        status = StatoPrenotazione.objects.get_or_create(nome='pending', defaults={'descrizione': 'In Attesa', 'colore': '#ffc107'})[0]
        Prenotazione.objects.create(
            utente=self.user,
            risorsa=self.risorsa,
            quantita=3,
            inizio=timezone.now() + timedelta(days=1),
            fine=timezone.now() + timedelta(days=1, hours=2),
            stato=status
        )

    def test_overbooking_blocked_by_default(self):
        inizio = timezone.now() + timedelta(days=1, minutes=15)
        fine = inizio + timedelta(hours=1)
        success, result = BookingService.create_booking(
            utente=self.user,
            risorsa_id=self.risorsa.id,
            quantita=3,
            inizio=inizio,
            fine=fine
        )
        self.assertFalse(success)

    def test_overbooking_allowed_when_enabled(self):
        # Enable overbooking with a small limit
        self.risorsa.allow_overbooking = True
        self.risorsa.overbooking_limite = 2
        self.risorsa.save()

        inizio = timezone.now() + timedelta(days=1, minutes=15)
        fine = inizio + timedelta(hours=1)
        # requesting 3 more when only 2 free -> should be blocked because limit 2
        success, result = BookingService.create_booking(
            utente=self.user,
            risorsa_id=self.risorsa.id,
            quantita=3,
            inizio=inizio,
            fine=fine
        )
        self.assertFalse(success)

        # requesting 2 (within overbooking limit) should succeed
        success2, result2 = BookingService.create_booking(
            utente=self.user,
            risorsa_id=self.risorsa.id,
            quantita=2,
            inizio=inizio,
            fine=fine
        )
        self.assertTrue(success2)
