from django.core.management.base import BaseCommand
from prenotazioni.services import NotificationService

class Command(BaseCommand):
    help = 'Process pending notifications (send emails, etc.)'

    def handle(self, *args, **options):
        self.stdout.write('Processing pending notifications...')
        try:
            NotificationService.send_pending_notifications()
            self.stdout.write(self.style.SUCCESS('Processing completed.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error processing notifications: {e}'))
