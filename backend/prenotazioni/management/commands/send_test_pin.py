from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings
import random
import string


class Command(BaseCommand):
    help = 'Invia un PIN di test all\'indirizzo specificato per verificare l\'invio email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email destinatario (es. i.nizzo@isufol.it)')

    def handle(self, *args, **options):
        email = options['email']
        pin = ''.join(random.choices(string.digits, k=6))
        subject = 'PIN di test'
        message = f'Questo è un test. Il PIN è: {pin}'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@isufol.it')
        try:
            send_mail(subject=subject, message=message, from_email=from_email, recipient_list=[email], fail_silently=False)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Errore invio email a {email}: {e}'))
            return
        self.stdout.write(self.style.SUCCESS(f'PIN inviato correttamente a {email}. PIN: {pin}'))
