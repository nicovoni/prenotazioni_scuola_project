"""
Comando Django per testare la configurazione email.
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Testa la configurazione email inviando un\'email di test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--destinatario',
            type=str,
            help='Indirizzo email del destinatario (default: admin email)',
        )

    def handle(self, *args, **options):
        destinatario = options.get('destinatario') or settings.ADMIN_EMAIL

        self.stdout.write(
            self.style.SUCCESS(f'Test configurazione email per {destinatario}')
        )

        # Mostra configurazione attuale
        self.stdout.write(f'HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'DEFAULT_FROM: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'PASSWORD_PRESENTE: {bool(settings.EMAIL_HOST_PASSWORD)}')

        try:
            # Utilizza lo stesso approccio migliorato con timeout lungo
            from django.core.mail.backends.smtp import EmailBackend
            from django.core.mail import EmailMessage

            backend = EmailBackend(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                timeout=60  # Timeout più lungo
            )

            # Crea e invia email di test
            email_message = EmailMessage(
                subject="Test configurazione email - Django",
                body="Questa è un'email di test inviata dal comando test_email.\n\nSe ricevi questa email, la configurazione SMTP è corretta!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[destinatario]
            )

            backend.send_messages([email_message])
            backend.close()

            self.stdout.write(
                self.style.SUCCESS(f'Email di test inviata con successo a {destinatario}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Errore invio email: {str(e)}')
            )
            logger.error(f'Errore test email: {e}')
