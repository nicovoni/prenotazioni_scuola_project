from config.celery import app
from django.utils import timezone

@app.task(bind=True, name='prenotazioni.tasks.send_notification')
def send_notification(self, notification_id):
    """Celery task: send a single notification by id.

    Loads the NotificaUtente instance and delegates to NotificationService._send_notification.
    """
    try:
        from .models import NotificaUtente
        from .services import NotificationService

        notification = NotificaUtente.objects.select_related('utente', 'template').get(id=notification_id)
        NotificationService._send_notification(notification)
    except Exception as e:
        # Let celery handle retries if desired
        raise


@app.task(bind=True, name='prenotazioni.tasks.process_pending_notifications')
def process_pending_notifications(self):
    """Celery task: process a batch of pending notifications."""
    try:
        from .services import NotificationService
        NotificationService.send_pending_notifications()
    except Exception:
        raise
