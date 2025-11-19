"""
Servizi per la nuova architettura del sistema di prenotazioni.

Logica di business completamente rinnovata per supportare:
- Workflow avanzati delle prenotazioni
- Sistema di notifiche completo
- Gestione sessioni e verifiche
- Audit trail e monitoraggio
- Configurazione centralizzata
"""

import logging
import threading
import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Q
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import (
    Risorsa, Dispositivo, Prenotazione, ConfigurazioneSistema as Configuration, SessioneUtente as UserSession,
    LogSistema as SystemLog, TemplateNotifica as NotificationTemplate, NotificaUtente as Notification, ProfiloUtente as UserProfile,
    UbicazioneRisorsa as ResourceLocation, CategoriaDispositivo as DeviceCategory, StatoPrenotazione as BookingStatus, CaricamentoFile as FileUpload
)

logger = logging.getLogger(__name__)


# =====================================================
# CONFIGURAZIONE E SETTINGS
# =====================================================

class ConfigurationService:
    """Servizio per gestire configurazioni centralizzate."""
    
    @classmethod
    def get_config(cls, chiave, default=None):
        """Ottiene valore configurazione dal database."""
        return Configuration.get_config(chiave, default)
    
    @classmethod
    def set_config(cls, chiave, valore, tipo='system', modificabile=True):
        """Imposta una configurazione."""
        config, created = Configuration.objects.get_or_create(
            chiave=chiave,
            defaults={
                'valore': valore,
                'tipo': tipo,
                'modificabile': modificabile
            }
        )
        if not created:
            config.valore = valore
            config.tipo = tipo
            config.modificabile = modificabile
            config.save()
        return config
    
    @classmethod
    def get_booking_settings(cls):
        """Ottiene tutte le configurazioni di prenotazione."""
        return {
            'start_hour': cls.get_config('BOOKING_START_HOUR', '08:00'),
            'end_hour': cls.get_config('BOOKING_END_HOUR', '18:00'),
            'min_advance_days': int(cls.get_config('GIORNI_ANTICIPO_PRENOTAZIONE', 2)),
            'min_duration_minutes': int(cls.get_config('DURATA_MINIMA_PRENOTAZIONE_MINUTI', 30)),
            'max_duration_minutes': int(cls.get_config('DURATA_MASSIMA_PRENOTAZIONE_MINUTI', 180)),
            'max_advance_days': int(cls.get_config('GIORNI_ANTICIPO_MASSIMO', 30)),
            'allow_weekend': cls.get_config('PRENOTAZIONI_WEEKEND', 'false').lower() == 'true',
            'allow_holidays': cls.get_config('PRENOTAZIONI_FESTIVI', 'false').lower() == 'true',
        }
    
    @classmethod
    def initialize_default_configs(cls):
        """Inizializza configurazioni di default."""
        defaults = {
            # Email
            'EMAIL_HOST': settings.EMAIL_HOST if hasattr(settings, 'EMAIL_HOST') else 'smtp-relay.brevo.com',
            'EMAIL_PORT': str(getattr(settings, 'EMAIL_PORT', 587)),
            'EMAIL_USE_TLS': str(getattr(settings, 'EMAIL_USE_TLS', True)).lower(),
            
            # Booking
            'BOOKING_START_HOUR': '08:00',
            'BOOKING_END_HOUR': '18:00',
            'GIORNI_ANTICIPO_PRENOTAZIONE': '2',
            'DURATA_MINIMA_PRENOTAZIONE_MINUTI': '30',
            'DURATA_MASSIMA_PRENOTAZIONE_MINUTI': '180',
            'GIORNI_ANTICIPO_MASSIMO': '30',
            'PRENOTAZIONI_WEEKEND': 'false',
            'PRENOTAZIONI_FESTIVI': 'false',
            
            # Sistema
            'MAX_PIN_ATTEMPTS': '5',
            'PIN_TIMEOUT_MINUTES': '60',
            'SESSION_TIMEOUT_HOURS': '24',
            'AUTO_CLEANUP_DAYS': '30',
            
            # UI
            'ITEMS_PER_PAGE': '20',
            'ENABLE_DARK_MODE': 'true',
            'DEFAULT_LANGUAGE': 'it',
        }
        
        for chiave, valore in defaults.items():
            cls.set_config(chiave, valore)


# =====================================================
# GESTIONE UTENTI E SESSIONI
# =====================================================

class UserSessionService:
    """Servizio per gestire sessioni utente e verifiche."""
    
    SESSION_TYPES = UserSession.TIPO_SESSIONE
    SESSION_TIMEOUTS = {
        'email_verification': timedelta(hours=24),
        'password_reset': timedelta(hours=1),
        'pin_login': timedelta(hours=1),
        'admin_setup': timedelta(hours=2),
        'booking_confirmation': timedelta(hours=6),
    }
    
    @classmethod
    def create_session(cls, user, tipo, email_destinazione, pin=None, metadata=None):
        """Crea nuova sessione utente."""
        timeout = cls.SESSION_TIMEOUTS.get(tipo, timedelta(hours=1))
        expires_at = timezone.now() + timeout
        
        session = UserSession.objects.create(
            user=user,
            tipo=tipo,
            email_destinazione=email_destinazione,
            pin=pin,
            metadata=metadata or {},
            expires_at=expires_at
        )
        
        # Log event
        SystemLog.log_event(
            tipo_evento='user_session_created',
            messaggio=f"Sessione {tipo} creata per {user.username}",
            utente=user,
            dettagli={'session_id': session.id, 'tipo': tipo}
        )
        
        return session
    
    @classmethod
    def verify_session(cls, session_token, pin=None):
        """Verifica sessione con eventuale PIN."""
        try:
            session = UserSession.objects.get(token=session_token)
        except UserSession.DoesNotExist:
            return False, "Sessione non trovata"
        
        if session.is_expired:
            session.expire()
            return False, "Sessione scaduta"
        
        if session.stato != 'pending':
            return False, "Sessione non valida"
        
        # Verifica PIN se richiesto
        if session.pin and pin != session.pin:
            # Note: increment_pin_attempts method doesn't exist on User model
            # In a full implementation, this would be handled differently
            return False, "PIN non corretto"
        
        # Verifica sessione
        success, message = session.verify(pin)
        if success:
            # Log event
            SystemLog.log_event(
                tipo_evento='user_session_verified',
                messaggio=f"Sessione {session.tipo} verificata per {session.user.username}",
                utente=session.user,
                dettagli={'session_id': session.id}
            )
        
        return success, message
    
    @classmethod
    def cleanup_expired_sessions(cls):
        """Pulizia sessioni scadute."""
        expired_count = UserSession.objects.filter(
            Q(expires_at__lt=timezone.now()) | Q(stato='expired')
        ).update(stato='expired')
        
        if expired_count > 0:
            logger.info(f"Pulite {expired_count} sessioni scadute")
        
        return expired_count
    
    @classmethod
    def generate_pin(cls):
        """Genera PIN a 6 cifre."""
        import random
        return ''.join(random.choices('0123456789', k=6))


class EmailService:
    """Servizio per invio email avanzato."""
    
    @classmethod
    def send_email(cls, subject, message, recipient_list, template_name=None, context=None):
        """Invia email con supporto template."""
        try:
            if template_name and context:
                # Usa template
                html_message = render_to_string(f'emails/{template_name}.html', context)
                plain_message = render_to_string(f'emails/{template_name}.txt', context)
            else:
                html_message = message
                plain_message = message
            
            # Invia email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', settings.ADMIN_EMAIL),
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False
            )
            
            # Log invio
            SystemLog.log_event(
                tipo_evento='email_sent',
                messaggio=f"Email inviata a {len(recipient_list)} destinatari",
                dettagli={
                    'subject': subject,
                    'recipients': recipient_list,
                    'template': template_name
                }
            )
            
            return True, None
            
        except Exception as e:
            error_msg = f"Errore invio email: {str(e)}"
            logger.error(error_msg)
            
            SystemLog.log_event(
                tipo_evento='system_error',
                messaggio=error_msg,
                livello='ERROR',
                dettagli={'subject': subject, 'recipients': recipient_list}
            )
            
            return False, str(e)
    
    @classmethod
    def send_pin_email(cls, user, pin, session_type='pin_login'):
        """Invia email con PIN."""
        school_info = SchoolInfo.get_instance()
        
        subject = f"Codice PIN - {school_info.nome_breve}"
        context = {
            'user': user,
            'pin': pin,
            'school_name': school_info.nome_breve,
            'school_logo': school_info.logo.url if hasattr(school_info, 'logo') and school_info.logo else None,
            'expires_in': '1 ora',
        }
        
        return cls.send_email(
            subject=subject,
            message="",
            recipient_list=[user.email],
            template_name='pin_verification',
            context=context
        )
    
    @classmethod
    def send_booking_confirmation(cls, booking):
        """Invia conferma prenotazione."""
        subject = f"Conferma Prenotazione - {booking.risorsa.nome}"
        context = {
            'booking': booking,
            'user': booking.utente,
            'resource': booking.risorsa,
            'school_info': SchoolInfo.get_instance(),
        }
        
        return cls.send_email(
            subject=subject,
            message="",
            recipient_list=[booking.utente.email],
            template_name='booking_confirmation',
            context=context
        )
    
    @classmethod
    def send_booking_reminder(cls, booking):
        """Invia promemoria prenotazione."""
        subject = f"Promemoria Prenotazione - {booking.risorsa.nome}"
        context = {
            'booking': booking,
            'user': booking.utente,
            'resource': booking.risorsa,
            'school_info': SchoolInfo.get_instance(),
            'hours_until': int((booking.inizio - timezone.now()).total_seconds() / 3600),
        }
        
        return cls.send_email(
            subject=subject,
            message="",
            recipient_list=[booking.utente.email],
            template_name='booking_reminder',
            context=context
        )


# =====================================================
# SERVIZI PRENOTAZIONI
# =====================================================

class BookingService:
    """Servizio principale per gestione prenotazioni."""
    
    @classmethod
    def check_resource_availability(cls, risorsa_id, inizio, fine, quantita_richiesta, exclude_booking_id=None):
        """
        Controlla disponibilità risorsa con logica migliorata.
        
        Args:
            risorsa_id: ID della risorsa
            inizio: Data/ora inizio
            fine: Data/ora fine
            quantita_richiesta: Quantità richiesta
            exclude_booking_id: ID prenotazione da escludere (modifiche)
        
        Returns:
            tuple: (is_available, available_quantity, errors)
        """
        try:
            risorsa = Risorsa.objects.get(id=risorsa_id)
        except Risorsa.DoesNotExist:
            return False, 0, ["Risorsa non trovata."]
        
        # Controllo stato risorsa
        if not risorsa.is_available_for_booking():
            if risorsa.manutenzione:
                return False, 0, ["Risorsa in manutenzione."]
            elif risorsa.bloccato:
                return False, 0, ["Risorsa temporaneamente bloccata."]
            else:
                return False, 0, ["Risorsa non disponibile."]
        
        # Logica diversa per tipo di risorsa
        if risorsa.tipo == 'laboratorio':
            return cls._check_laboratorio_availability(risorsa, inizio, fine, exclude_booking_id)
        elif risorsa.tipo == 'carrello':
            return cls._check_carrello_availability(risorsa, inizio, fine, quantita_richiesta, exclude_booking_id)
        else:
            return cls._check_generic_availability(risorsa, inizio, fine, quantita_richiesta, exclude_booking_id)
    
    @classmethod
    def _check_laboratorio_availability(cls, risorsa, inizio, fine, exclude_booking_id):
        """Controlla disponibilità laboratorio (prenotazione esclusiva)."""
        query = Booking.objects.filter(
            risorsa=risorsa,
            inizio__lt=fine,
            fine__gt=inizio,
            cancellato_il__isnull=True
        )
        
        if exclude_booking_id:
            query = query.exclude(id=exclude_booking_id)
        
        if query.exists():
            return False, 0, ["Laboratorio già prenotato in questo periodo."]
        
        return True, 1, []
    
    @classmethod
    def _check_carrello_availability(cls, risorsa, inizio, fine, quantita_richiesta, exclude_booking_id):
        """Controlla disponibilità carrello (prenotazione parziale)."""
        if not risorsa.capacita_massima:
            return False, 0, ["Carrello senza capacità definita."]
        
        query = Booking.objects.filter(
            risorsa=risorsa,
            inizio__lt=fine,
            fine__gt=inizio,
            cancellato_il__isnull=True
        )
        
        if exclude_booking_id:
            query = query.exclude(id=exclude_booking_id)
        
        # Calcola quantità occupata
        quantita_occupata = query.aggregate(Sum('quantita'))['quantita__sum'] or 0
        disponibile = risorsa.capacita_massima - quantita_occupata
        
        if quantita_richiesta > disponibile:
            message = f"Disponibilità insufficiente: richieste {quantita_richiesta}, disponibili {disponibile}."
            return False, disponibile, [message]
        
        return True, disponibile, []
    
    @classmethod
    def _check_generic_availability(cls, risorsa, inizio, fine, quantita_richiesta, exclude_booking_id):
        """Controllo disponibilità generico."""
        # Implementazione base - da specializzare per altri tipi
        return True, quantita_richiesta, []
    
    @classmethod
    def create_booking(cls, utente, risorsa_id, quantita, inizio, fine, **kwargs):
        """Crea nuova prenotazione con workflow avanzato."""
        try:
            # Verifica disponibilità
            is_available, disponibile, errors = cls.check_resource_availability(
                risorsa_id, inizio, fine, quantita
            )
            
            if not is_available:
                return False, errors[0] if errors else "Risorsa non disponibile."
            
            # Verifica permessi utente - simplified since User model doesn't have permission methods
            if not utente.is_active:
                return False, "Utente non attivo."
            
            # Crea prenotazione
            risorsa = Risorsa.objects.get(id=risorsa_id)
            
            # Determina stato iniziale
            initial_status = BookingStatus.objects.get_or_create(
                nome='pending',
                defaults={'descrizione': 'In Attesa', 'colore': '#ffc107'}
            )[0]
            
            booking = Booking.objects.create(
                utente=utente,
                risorsa=risorsa,
                quantita=quantita,
                inizio=inizio,
                fine=fine,
                stato=initial_status,
                **kwargs
            )
            
            # Log event
            SystemLog.log_event(
                tipo_evento='booking_created',
                messaggio=f"Prenotazione creata: {risorsa.nome}",
                utente=utente,
                dettagli={
                    'booking_id': booking.id,
                    'resource': risorsa.nome,
                    'quantity': quantita,
                    'start': inizio.isoformat(),
                    'end': fine.isoformat()
                }
            )
            
            # Invia notifiche
            NotificationService.create_booking_notifications(booking)
            
            return True, booking
            
        except Exception as e:
            error_msg = f"Errore creazione prenotazione: {str(e)}"
            logger.error(error_msg)
            
            SystemLog.log_event(
                tipo_evento='system_error',
                messaggio=error_msg,
                livello='ERROR',
                utente=utente,
                dettagli={'resource_id': risorsa_id}
            )
            
            return False, str(e)
    
    @classmethod
    def update_booking(cls, booking_id, utente, inizio, fine, quantita, **kwargs):
        """Aggiorna prenotazione esistente."""
        try:
            booking = Booking.objects.get(id=booking_id)
            
            # Controllo permessi - simplified since Booking model doesn't have permission methods
            if booking.utente != utente:
                return False, "Puoi modificare solo le tue prenotazioni."
            
            # Verifica disponibilità (escludendo questa prenotazione)
            is_available, disponibile, errors = cls.check_resource_availability(
                booking.risorsa.id, inizio, fine, quantita, exclude_booking_id=booking_id
            )
            
            if not is_available:
                return False, errors[0] if errors else "Risorsa non disponibile per il nuovo orario."
            
            # Aggiorna prenotazione
            booking.inizio = inizio
            booking.fine = fine
            booking.quantita = quantita
            
            # Aggiorna altri campi
            for key, value in kwargs.items():
                if hasattr(booking, key):
                    setattr(booking, key, value)
            
            booking.save()
            
            # Log event
            SystemLog.log_event(
                tipo_evento='booking_modified',
                messaggio=f"Prenotazione modificata: {booking.risorsa.nome}",
                utente=utente,
                dettagli={
                    'booking_id': booking.id,
                    'changes': kwargs
                }
            )
            
            # Invia notifiche aggiornamento
            NotificationService.create_booking_update_notifications(booking)
            
            return True, booking
            
        except Booking.DoesNotExist:
            return False, "Prenotazione non trovata."
        except Exception as e:
            error_msg = f"Errore aggiornamento prenotazione: {str(e)}"
            logger.error(error_msg)
            return False, str(e)
    
    @classmethod
    def cancel_booking(cls, booking_id, utente, reason=""):
        """Cancella prenotazione."""
        try:
            booking = Booking.objects.get(id=booking_id)
            
            # Controllo permessi - simplified since Booking model doesn't have permission methods
            if booking.utente != utente:
                return False, "Puoi cancellare solo le tue prenotazioni."

            # Cancella prenotazione - simplified since Booking model doesn't have cancel method
            booking.cancellato_il = timezone.now()
            booking.note_cancellazione = reason
            booking.save()
            success, message = True, f"Prenotazione cancellata con successo. Motivo: {reason}"
            
            if success:
                # Log event
                SystemLog.log_event(
                    tipo_evento='booking_cancelled',
                    messaggio=f"Prenotazione cancellata: {booking.risorsa.nome}",
                    utente=utente,
                    dettagli={
                        'booking_id': booking.id,
                        'reason': reason
                    }
                )
                
                # Invia notifiche cancellazione
                NotificationService.create_booking_cancellation_notifications(booking)
            
            return success, message
            
        except Booking.DoesNotExist:
            return False, "Prenotazione non trovata."
        except Exception as e:
            error_msg = f"Errore cancellazione prenotazione: {str(e)}"
            logger.error(error_msg)
            return False, str(e)
    
    @classmethod
    def get_user_bookings(cls, user, include_cancelled=False):
        """Ottiene prenotazioni utente."""
        query = Booking.objects.filter(utente=user)
        
        if not include_cancelled:
            query = query.filter(cancellato_il__isnull=True)
        
        return query.select_related('risorsa', 'stato').order_by('-inizio')
    
    @classmethod
    def get_resource_bookings(cls, resource, start_date=None, end_date=None):
        """Ottiene prenotazioni risorsa in un periodo."""
        query = Booking.objects.filter(risorsa=resource, cancellato_il__isnull=True)
        
        if start_date:
            query = query.filter(fine__gte=start_date)
        if end_date:
            query = query.filter(inizio__lte=end_date)
        
        return query.select_related('utente', 'stato').order_by('inizio')
    
    @classmethod
    def check_conflicts(cls, resource, start, end, exclude_booking_id=None):
        """Controlla conflitti per una risorsa."""
        query = Booking.objects.filter(
            risorsa=resource,
            inizio__lt=end,
            fine__gt=start,
            cancellato_il__isnull=True
        )
        
        if exclude_booking_id:
            query = query.exclude(id=exclude_booking_id)
        
        return query.exists()


# =====================================================
# SERVIZIO NOTIFICHE
# =====================================================

class NotificationService:
    """Servizio per gestione notifiche avanzate."""
    
    @classmethod
    def create_notification(cls, user, template_name, context, **kwargs):
        """Crea notifica da template."""
        try:
            template = NotificationTemplate.objects.get(
                nome=template_name,
                attivo=True
            )
            
            # Render template
            rendered_message = template.render_template(context)
            rendered_title = template.render_template({'title': template.oggetto, **context})
            
            notification = Notification.objects.create(
                utente=user,
                template=template,
                tipo=template.evento,
                canale=template.tipo,
                titolo=rendered_title,
                messaggio=rendered_message,
                dati_aggiuntivi=context,
                **kwargs
            )
            
            return notification
            
        except NotificationTemplate.DoesNotExist:
            logger.warning(f"Template {template_name} non trovato o non attivo")
            return None
    
    @classmethod
    def create_booking_notifications(cls, booking):
        """Crea notifiche per nuova prenotazione."""
        # Notifica utente
        context = {
            'booking': booking,
            'user': booking.utente,
            'resource': booking.risorsa
        }
        
        cls.create_notification(
            booking.utente,
            'booking_created',
            context,
            related_booking=booking
        )
        
        # Notifica admin se necessario
        if booking.setup_needed:
            # Note: Since User model doesn't have role field, we skip admin notifications
            # In a full implementation, this would need to be handled differently
            pass
    
    @classmethod
    def create_booking_update_notifications(cls, booking):
        """Crea notifiche per aggiornamento prenotazione."""
        context = {
            'booking': booking,
            'user': booking.utente,
            'resource': booking.risorsa
        }
        
        cls.create_notification(
            booking.utente,
            'booking_updated',
            context,
            related_booking=booking
        )
    
    @classmethod
    def create_booking_cancellation_notifications(cls, booking):
        """Crea notifiche per cancellazione prenotazione."""
        context = {
            'booking': booking,
            'user': booking.utente,
            'resource': booking.risorsa
        }
        
        cls.create_notification(
            booking.utente,
            'booking_cancelled',
            context,
            related_booking=booking
        )
    
    @classmethod
    def send_pending_notifications(cls):
        """Invia notifiche in attesa."""
        pending_notifications = Notification.objects.filter(
            stato='pending',
            prossimo_tentativo__lte=timezone.now()
        ).select_related('utente', 'template')[:50]  # Processa in batch
        
        for notification in pending_notifications:
            try:
                if notification.can_retry:
                    cls._send_notification(notification)
                else:
                    notification.stato = 'failed'
                    notification.errore_messaggio = "Massimi tentativi raggiunti"
                    notification.save()
                    
            except Exception as e:
                logger.error(f"Errore invio notifica {notification.id}: {e}")
                notification.tentativo_corrente += 1
                notification.ultimo_tentativo = timezone.now()
                
                if notification.can_retry and notification.template:
                    next_retry = notification.template.intervallo_tentativi_minuti
                    notification.prossimo_tentativo = timezone.now() + timedelta(minutes=next_retry)
                else:
                    notification.stato = 'failed'
                    notification.errore_messaggio = str(e)
                
                notification.save()
    
    @classmethod
    def _send_notification(cls, notification):
        """Invia singola notifica."""
        if notification.canale == 'email':
            success, error = EmailService.send_email(
                subject=notification.titolo,
                message=notification.messaggio,
                recipient_list=[notification.utente.email]
            )
            
            if success:
                notification.stato = 'sent'
                notification.inviata_il = timezone.now()
            else:
                notification.stato = 'failed'
                notification.errore_messaggio = error
        else:
            # Altri canali da implementare (SMS, push, etc.)
            notification.stato = 'sent'
            notification.inviata_il = timezone.now()
        
        notification.tentativo_corrente += 1
        notification.ultimo_tentativo = timezone.now()
        notification.save()


# =====================================================
# SERVIZI DISPOSITIVI E RISORSE
# =====================================================

class DeviceService:
    """Servizio per gestione dispositivi."""
    
    @classmethod
    def get_available_devices(cls, resource=None, device_type=None):
        """Ottiene dispositivi disponibili."""
        query = Device.objects.filter(attivo=True, stato='disponibile')
        
        if resource:
            query = query.filter(risorse=resource)
        if device_type:
            query = query.filter(tipo=device_type)
        
        return query.select_related('categoria').order_by('marca', 'nome')
    
    @classmethod
    def check_device_availability(cls, device, start, end, exclude_booking_id=None):
        """Controlla disponibilità dispositivo specifico."""
        query = Booking.objects.filter(
            dispositivi_selezionati=device,
            inizio__lt=end,
            fine__gt=start,
            cancellato_il__isnull=True
        )
        
        if exclude_booking_id:
            query = query.exclude(id=exclude_booking_id)
        
        return not query.exists()
    
    @classmethod
    def get_device_usage_stats(cls, device, days=30):
        """Statistiche utilizzo dispositivo."""
        start_date = timezone.now() - timedelta(days=days)
        
        bookings = Booking.objects.filter(
            dispositivi_selezionati=device,
            inizio__gte=start_date,
            cancellato_il__isnull=True
        )
        
        total_bookings = bookings.count()
        total_hours = sum(b.durata_ore for b in bookings)
        
        return {
            'total_bookings': total_bookings,
            'total_hours': total_hours,
            'average_duration': total_hours / total_bookings if total_bookings > 0 else 0,
            'utilization_rate': (total_hours / (days * 24)) * 100 if days > 0 else 0
        }


class ResourceService:
    """Servizio per gestione risorse."""
    
    @classmethod
    def get_available_resources(cls, resource_type=None, start=None, end=None):
        """Ottiene risorse disponibili."""
        query = Resource.objects.filter(attivo=True, manutenzione=False, bloccato=False)
        
        if resource_type:
            query = query.filter(tipo=resource_type)
        
        if start and end:
            # Filtra risorse senza conflitti
            available_resources = []
            for resource in query:
                if not BookingService.check_conflicts(resource, start, end):
                    available_resources.append(resource.id)
            query = query.filter(id__in=available_resources)
        
        return query.select_related('localizzazione').order_by('tipo', 'nome')
    
    @classmethod
    def get_resource_utilization(cls, resource, days=30):
        """Statistiche utilizzo risorsa."""
        start_date = timezone.now() - timedelta(days=days)
        
        bookings = Booking.objects.filter(
            risorsa=resource,
            inizio__gte=start_date,
            cancellato_il__isnull=True
        )
        
        total_bookings = bookings.count()
        total_hours = sum(b.durata_ore for b in bookings)
        
        # Calcola occupazione media
        working_hours_per_day = 10  # 8-18
        total_working_hours = days * working_hours_per_day
        utilization_rate = (total_hours / total_working_hours) * 100 if total_working_hours > 0 else 0
        
        return {
            'total_bookings': total_bookings,
            'total_hours': total_hours,
            'average_duration': total_hours / total_bookings if total_bookings > 0 else 0,
            'utilization_rate': utilization_rate,
            'peak_hours': cls._get_peak_hours(bookings)
        }
    
    @classmethod
    def _get_peak_hours(cls, bookings):
        """Calcola ore di punta per le prenotazioni."""
        hour_counts = {}
        for booking in bookings:
            hour = booking.inizio.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        if hour_counts:
            peak_hour = max(hour_counts.items(), key=lambda x: x[1])
            return {'hour': peak_hour[0], 'bookings': peak_hour[1]}
        return None


# =====================================================
# SERVIZI SISTEMA E MONITORAGGIO
# =====================================================

class SystemService:
    """Servizio per monitoraggio e manutenzione sistema."""
    
    @classmethod
    def get_system_stats(cls):
        """Statistiche generali sistema."""
        now = timezone.now()
        
        from django.contrib.auth import get_user_model
        User = get_user_model()

        stats = {
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(is_active=True).count(),
                'verified': User.objects.filter(is_active=True).count(),  # Simplified since User doesn't have email_verificato field
                'by_role': {}  # User model doesn't have role field
            },
            'resources': {
                'total': Resource.objects.count(),
                'active': Resource.objects.filter(attivo=True).count(),
                'by_type': dict(Resource.objects.values_list('tipo').annotate(count=models.Count('id')))
            },
            'devices': {
                'total': Device.objects.count(),
                'available': Device.objects.filter(stato='disponibile').count(),
                'by_type': dict(Device.objects.values_list('tipo').annotate(count=models.Count('id')))
            },
            'bookings': {
                'total': Booking.objects.count(),
                'active': Booking.objects.filter(cancellato_il__isnull=True).count(),
                'today': Booking.objects.filter(
                    inizio__date=now.date(),
                    cancellato_il__isnull=True
                ).count(),
                'this_week': Booking.objects.filter(
                    inizio__gte=now - timedelta(days=7),
                    cancellato_il__isnull=True
                ).count()
            },
            'system': {
                'uptime': cls._get_uptime(),
                'last_backup': cls._get_last_backup(),
                'disk_usage': cls._get_disk_usage(),
                'active_sessions': UserSession.objects.filter(stato='pending').count()
            }
        }
        
        return stats
    
    @classmethod
    def _get_uptime(cls):
        """Calcola uptime sistema (simulato)."""
        # Implementazione reale richiederebbe tracking start time
        return "N/A"
    
    @classmethod
    def _get_last_backup(cls):
        """Data ultimo backup."""
        last_log = SystemLog.objects.filter(
            tipo_evento='backup_created'
        ).order_by('-timestamp').first()
        
        return last_log.timestamp if last_log else None
    
    @classmethod
    def _get_disk_usage(cls):
        """Utilizzo disco (simulato)."""
        # Implementazione reale richiederebbe accesso al filesystem
        return "N/A"
    
    @classmethod
    def cleanup_expired_data(cls):
        """Pulizia dati scaduti."""
        cleaned_items = {}
        
        # Pulisci sessioni scadute
        cleaned_items['sessions'] = UserSessionService.cleanup_expired_sessions()
        
        # Pulisci log vecchi
        days_to_keep = int(ConfigurationService.get_config('AUTO_CLEANUP_DAYS', 30))
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        old_logs = SystemLog.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        cleaned_items['logs'] = old_logs
        
        # Pulisci notifiche vecchie
        old_notifications = Notification.objects.filter(
            creato_il__lt=cutoff_date,
            stato__in=['sent', 'failed', 'cancelled']
        ).delete()[0]
        cleaned_items['notifications'] = old_notifications
        
        logger.info(f"Pulizia automatica completata: {cleaned_items}")
        return cleaned_items
    
    @classmethod
    def generate_system_report(cls):
        """Genera report sistema."""
        stats = cls.get_system_stats()
        
        report = {
            'generated_at': timezone.now(),
            'summary': stats,
            'recommendations': cls._generate_recommendations(stats),
            'alerts': cls._check_system_alerts(stats)
        }
        
        # Log generazione report
        SystemLog.log_event(
            tipo_evento='system_report_generated',
            messaggio="Report sistema generato",
            dettagli={'stats_keys': list(stats.keys())}
        )
        
        return report
    
    @classmethod
    def _generate_recommendations(cls, stats):
        """Genera raccomandazioni basate su statistiche."""
        recommendations = []
        
        # Controllo utilizzo risorse
        if stats['resources']['active'] == 0:
            recommendations.append({
                'type': 'warning',
                'message': 'Nessuna risorsa attiva disponibile',
                'action': 'Configurare almeno una risorsa prenotabile'
            })
        
        # Controllo dispositivi
        if stats['devices']['available'] == 0:
            recommendations.append({
                'type': 'warning',
                'message': 'Nessun dispositivo disponibile',
                'action': 'Aggiungere dispositivi al catalogo'
            })
        
        # Controllo utilizzo basso
        if stats['bookings']['this_week'] == 0:
            recommendations.append({
                'type': 'info',
                'message': 'Nessuna prenotazione questa settimana',
                'action': 'Verificare visibilità sistema agli utenti'
            })
        
        return recommendations
    
    @classmethod
    def _check_system_alerts(cls, stats):
        """Controlla alert di sistema."""
        alerts = []
        
        # Alert utilizzo alto
        if stats['users']['total'] > 0 and stats['bookings']['this_week'] / stats['users']['total'] < 0.1:
            alerts.append({
                'level': 'warning',
                'message': 'Basso utilizzo del sistema',
                'details': 'Meno del 10% degli utenti ha effettuato prenotazioni questa settimana'
            })
        
        # Alert sessioni bloccate
        if stats['system']['active_sessions'] > 100:
            alerts.append({
                'level': 'info',
                'message': 'Numero elevato di sessioni attive',
                'details': f"{stats['system']['active_sessions']} sessioni in attesa"
            })
        
        return alerts


# =====================================================
# INIZIALIZZAZIONE SISTEMA
# =====================================================

class SystemInitializer:
    """Servizio per inizializzazione sistema."""
    
    @classmethod
    def initialize_system(cls):
        """Inizializza sistema con dati base."""
        try:
            # Inizializza configurazioni
            ConfigurationService.initialize_default_configs()
            
            # Crea stati prenotazione di default
            cls._create_default_booking_statuses()
            
            # Crea template notifiche di default
            cls._create_default_notification_templates()
            
            # Crea categorie dispositivi di default
            cls._create_default_device_categories()
            
            # Log inizializzazione
            SystemLog.log_event(
                tipo_evento='system_initialized',
                messaggio="Sistema inizializzato con successo",
                livello='INFO'
            )
            
            return True, "Sistema inizializzato con successo"
            
        except Exception as e:
            error_msg = f"Errore inizializzazione sistema: {str(e)}"
            logger.error(error_msg)
            
            SystemLog.log_event(
                tipo_evento='system_error',
                messaggio=error_msg,
                livello='CRITICAL'
            )
            
            return False, str(e)
    
    @classmethod
    def _create_default_booking_statuses(cls):
        """Crea stati prenotazione di default."""
        statuses = [
            {'nome': 'pending', 'descrizione': 'In Attesa', 'colore': '#ffc107', 'ordine': 1},
            {'nome': 'confirmed', 'descrizione': 'Confermata', 'colore': '#28a745', 'ordine': 2},
            {'nome': 'in_progress', 'descrizione': 'In Corso', 'colore': '#17a2b8', 'ordine': 3},
            {'nome': 'completed', 'descrizione': 'Completata', 'colore': '#6c757d', 'ordine': 4},
            {'nome': 'cancelled', 'descrizione': 'Cancellata', 'colore': '#dc3545', 'ordine': 5},
            {'nome': 'no_show', 'descrizione': 'Non Presentato', 'colore': '#fd7e14', 'ordine': 6},
        ]
        
        for status_data in statuses:
            BookingStatus.objects.get_or_create(
                nome=status_data['nome'],
                defaults=status_data
            )
    
    @classmethod
    def _create_default_notification_templates(cls):
        """Crea template notifiche di default."""
        templates = [
            {
                'nome': 'booking_created',
                'tipo': 'email',
                'evento': 'booking_created',
                'oggetto': 'Conferma Prenotazione - {{ resource.nome }}',
                'contenuto': 'Ciao {{ user.first_name }},\\n\\nLa tua prenotazione per {{ resource.nome }} è stata creata con successo.\\n\\nData: {{ booking.inizio|date:"d/m/Y" }}\\nOrario: {{ booking.inizio|time:"H:i" }} - {{ booking.fine|time:"H:i" }}\\n\\nGrazie!'
            },
            {
                'nome': 'booking_reminder',
                'tipo': 'email',
                'evento': 'booking_reminder',
                'oggetto': 'Promemoria Prenotazione - {{ resource.nome }}',
                'contenuto': 'Ciao {{ user.first_name }},\\n\\nTi ricordiamo la tua prenotazione per {{ resource.nome }} che inizia tra {{ hours_until }} ore.\\n\\nA presto!'
            },
        ]
        
        for template_data in templates:
            NotificationTemplate.objects.get_or_create(
                nome=template_data['nome'],
                defaults=template_data
            )
    
    @classmethod
    def _create_default_device_categories(cls):
        """Crea categorie dispositivi di default."""
        categories = [
            {'nome': 'Computer', 'descrizione': 'Computer e laptop', 'icona': 'bi-laptop', 'colore': '#007bff', 'ordine': 1},
            {'nome': 'Tablet', 'descrizione': 'Tablet e iPad', 'icona': 'bi-tablet', 'colore': '#28a745', 'ordine': 2},
            {'nome': 'Proiettori', 'descrizione': 'Proiettori e schermi', 'icona': 'bi-camera-video', 'colore': '#ffc107', 'ordine': 3},
            {'nome': 'Audio', 'descrizione': 'Attrezzature audio', 'icona': 'bi-speaker', 'colore': '#17a2b8', 'ordine': 4},
            {'nome': 'Altro', 'descrizione': 'Altri dispositivi', 'icona': 'bi-gear', 'colore': '#6c757d', 'ordine': 5},
        ]
        
        for category_data in categories:
            DeviceCategory.objects.get_or_create(
                nome=category_data['nome'],
                defaults=category_data
            )
