"""
Servizi per la logica di business delle prenotazioni.
Estraggono la logica complessa dalle views per migliorare manutenibilità.
"""
import logging
import threading
from django.utils import timezone
from django.db.models import Sum
from django.core.mail import send_mail
from django.conf import settings
from .models import Prenotazione, Risorsa

logger = logging.getLogger(__name__)


class BookingService:
    """Servizio per la gestione delle prenotazioni."""

    @staticmethod
    def validate_booking_data(laboratorio_id, data, ora_inizio, ora_fine, quantita):
        """
        Valida i dati di prenotazione.

        Args:
            laboratorio_id: ID del laboratorio
            data: Data prenotazione (YYYY-MM-DD)
            ora_inizio: Ora inizio (HH:MM)
            ora_fine: Ora fine (HH:MM)
            quantita: Quantità richiesta

        Returns:
            tuple: (is_valid, errors_list, parsed_datetime_objects)
        """
        errors = []

        # Controlli campi obbligatori
        if not laboratorio_id:
            errors.append("Seleziona un laboratorio.")
        if not data:
            errors.append("Seleziona una data.")
        if not ora_inizio or not ora_fine:
            errors.append("Seleziona orario di inizio e fine.")

        inizio = fine = None
        if data and ora_inizio and ora_fine:
            try:
                inizio = timezone.datetime.strptime(f"{data} {ora_inizio}", "%Y-%m-%d %H:%M")
                fine = timezone.datetime.strptime(f"{data} {ora_fine}", "%Y-%m-%d %H:%M")
                inizio = timezone.make_aware(inizio)
                fine = timezone.make_aware(fine)
                now = timezone.now()

                # Validazioni temporali
                if inizio < now:
                    errors.append("La data e ora di inizio devono essere nel futuro.")

                giorni_anticipo = settings.GIORNI_ANTICIPO_PRENOTAZIONE
                if (inizio.date() - now.date()).days < giorni_anticipo:
                    errors.append(f"La prenotazione deve essere fatta almeno {giorni_anticipo} giorni prima.")

                # Controllo orari consentiti
                orario_inizio = inizio.strftime('%H:%M')
                orario_fine = fine.strftime('%H:%M')
                if orario_inizio < settings.BOOKING_START_HOUR or orario_fine > settings.BOOKING_END_HOUR:
                    errors.append(f"Le prenotazioni sono consentite solo tra le {settings.BOOKING_START_HOUR} e le {settings.BOOKING_END_HOUR}.")

                # Controllo durata
                durata_min = settings.DURATA_MINIMA_PRENOTAZIONE_MINUTI
                durata_max = settings.DURATA_MASSIMA_PRENOTAZIONE_MINUTI
                durata = int((fine - inizio).total_seconds() // 60)

                if durata < durata_min:
                    errors.append(f"La durata minima della prenotazione è di {durata_min} minuti.")
                if durata > durata_max:
                    errors.append(f"La durata massima della prenotazione è di {durata_max} minuti.")
                if fine <= inizio:
                    errors.append("L'orario di fine deve essere successivo a quello di inizio.")

            except ValueError:
                errors.append("Data o orario non validi.")

        return len(errors) == 0, errors, (inizio, fine)

    @staticmethod
    def check_resource_availability(risorsa_id, inizio, fine, quantita_richiesta, exclude_booking_id=None):
        """
        Controlla la disponibilità di una risorsa.

        Args:
            risorsa_id: ID della risorsa
            inizio: Data/ora inizio
            fine: Data/ora fine
            quantita_richiesta: Quantità richiesta
            exclude_booking_id: ID prenotazione da escludere (per modifiche)

        Returns:
            tuple: (is_available, available_quantity, errors)
        """
        try:
            risorsa = Risorsa.objects.get(id=risorsa_id)

            # Logica diversa per tipo di risorsa
            if risorsa.tipo == 'lab':
                # Per i laboratori: controllo se è già prenotato in quel periodo
                # La quantità deve essere 1 (intero laboratorio)
                overlapping = Prenotazione.objects.filter(risorsa_id=risorsa_id)
                if exclude_booking_id:
                    overlapping = overlapping.exclude(pk=exclude_booking_id)
                overlapping = overlapping.filter(inizio__lt=fine, fine__gt=inizio)

                if overlapping.exists():
                    return False, 0, ["Laboratorio già prenotato in questo periodo."]
                else:
                    return True, 1, []

            elif risorsa.tipo == 'carrello':
                # Per i carrelli: controllo disponibilità parziale
                totale = risorsa.quantita_totale or 1

                # Query prenotazioni sovrapposte
                overlapping = Prenotazione.objects.filter(risorsa_id=risorsa_id)
                if exclude_booking_id:
                    overlapping = overlapping.exclude(pk=exclude_booking_id)
                overlapping = overlapping.filter(inizio__lt=fine, fine__gt=inizio)

                somma_occupata = overlapping.aggregate(Sum('quantita'))['quantita__sum'] or 0
                disponibile = totale - somma_occupata

                if quantita_richiesta > disponibile:
                    return False, disponibile, [f"Disponibilità insufficiente: richieste {quantita_richiesta}, disponibili {disponibile}."]

                return True, disponibile, []
            else:
                return False, 0, ["Tipo di risorsa non supportato."]

        except Risorsa.DoesNotExist:
            return False, 0, ["Risorsa non trovata."]

    @staticmethod
    def create_booking(utente, risorsa_id, quantita, inizio, fine):
        """
        Crea una nuova prenotazione.

        Args:
            utente: Utente che prenota
            risorsa_id: ID risorsa
            quantita: Quantità
            inizio: Data/ora inizio
            fine: Data/ora fine

        Returns:
            tuple: (success, prenotazione_or_errors)
        """
        try:
            prenotazione = Prenotazione.objects.create(
                utente=utente,
                risorsa_id=risorsa_id,
                quantita=quantita,
                inizio=inizio,
                fine=fine
            )

            logger.info(f"Prenotazione creata: {prenotazione}")

            # Invia email di conferma
            success, error = EmailService.send_booking_confirmation(prenotazione)
            if not success:
                logger.warning(f"Errore invio email conferma: {error}")

            return True, prenotazione

        except Exception as e:
            logger.error(f"Errore creazione prenotazione: {e}")
            return False, [f"Errore durante la creazione: {str(e)}"]

    @staticmethod
    def update_booking(prenotazione_id, utente, inizio, fine, quantita):
        """
        Aggiorna una prenotazione esistente.

        Args:
            prenotazione_id: ID prenotazione
            utente: Utente che esegue l'operazione (può essere proprietario o admin)
            inizio: Nuovo inizio
            fine: Nuova fine
            quantita: Nuova quantità

        Returns:
            tuple: (success, prenotazione_or_errors)
        """
        try:
            prenotazione = Prenotazione.objects.get(pk=prenotazione_id)

            # Controllo autorizzazioni: admin può modificare qualsiasi prenotazione, altri solo le proprie
            if not utente.is_admin() and prenotazione.utente != utente:
                return False, ["Non hai i permessi per modificare questa prenotazione."]

            # Controllo disponibilità escludendo questa prenotazione
            is_available, _, errors = BookingService.check_resource_availability(
                prenotazione.risorsa_id, inizio, fine, quantita, exclude_booking_id=prenotazione_id
            )

            if not is_available:
                return False, errors

            # Aggiornamento
            prenotazione.inizio = inizio
            prenotazione.fine = fine
            prenotazione.quantita = quantita
            prenotazione.save()

            logger.info(f"Prenotazione aggiornata: {prenotazione}")
            return True, prenotazione

        except Prenotazione.DoesNotExist:
            return False, ["Prenotazione non trovata."]
        except Exception as e:
            logger.error(f"Errore aggiornamento prenotazione: {e}")
            return False, [f"Errore durante l'aggiornamento: {str(e)}"]

    @staticmethod
    def delete_booking(prenotazione_id, utente):
        """
        Elimina una prenotazione.

        Args:
            prenotazione_id: ID prenotazione
            utente: Utente che esegue l'operazione (può essere proprietario o admin)

        Returns:
            tuple: (success, errors)
        """
        try:
            prenotazione = Prenotazione.objects.get(pk=prenotazione_id)

            # Controllo autorizzazioni: admin può eliminare qualsiasi prenotazione, altri solo le proprie
            if not utente.is_admin() and prenotazione.utente != utente:
                return False, ["Non hai i permessi per eliminare questa prenotazione."]

            prenotazione.delete()
            logger.info(f"Prenotazione eliminata: {prenotazione_id} da utente {utente}")
            return True, []

        except Prenotazione.DoesNotExist:
            return False, ["Prenotazione non trovata."]
        except Exception as e:
            logger.error(f"Errore eliminazione prenotazione: {e}")
            return False, [f"Errore durante l'eliminazione: {str(e)}"]


class EmailService:
    """Servizio per l'invio di email."""

    @staticmethod
    def send_booking_confirmation_async(prenotazione):
        """
        Invia email di conferma prenotazione in modo asincrono.

        Args:
            prenotazione: Oggetto prenotazione
        """
        def _send():
            subject = f"Conferma prenotazione: {prenotazione.risorsa.nome}"
            message = (
                f"Ciao {prenotazione.utente.first_name or prenotazione.utente.username},\n\n"
                f"La tua prenotazione per {prenotazione.risorsa.nome} è stata confermata.\n"
                f"Data: {prenotazione.inizio.date()}\n"
                f"Orario: {prenotazione.inizio.time().strftime('%H:%M')} - {prenotazione.fine.time().strftime('%H:%M')}\n"
                f"Quantità: {prenotazione.quantita}\n\n"
                "Grazie per aver utilizzato il sistema di prenotazioni. Buona giornata!"
            )

            try:
                logger.info(f"=== INVIO EMAIL CONFERMA PRENOTAZIONE ===")
                logger.info(f"Destinatario: {prenotazione.utente.email}")
                logger.info(f"Prenotazione: {prenotazione.id} - {prenotazione.risorsa.nome}")

                # Use direct SMTP backend with shorter timeout
                from django.core.mail.backends.smtp import EmailBackend
                from django.core.mail import EmailMessage

                backend = EmailBackend(
                    host=settings.EMAIL_HOST,
                    port=settings.EMAIL_PORT,
                    username=settings.EMAIL_HOST_USER,
                    password=settings.EMAIL_HOST_PASSWORD,
                    use_tls=settings.EMAIL_USE_TLS,
                    timeout=10  # Short timeout to avoid hanging
                )

                email_message = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[prenotazione.utente.email]
                )

                backend.send_messages([email_message])
                backend.close()

                logger.info(f"Email conferma inviata con SUCCESSO a {prenotazione.utente.email}")

            except Exception as e:
                logger.error(f"Errore invio email conferma a {prenotazione.utente.email}: {str(e)}")
                # Don't log sensitive config in production
                if settings.DEBUG:
                    logger.error(f"Configurazione SMTP: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}")

        thread = threading.Thread(target=_send)
        thread.daemon = True
        thread.start()

    @staticmethod
    def send_booking_confirmation(prenotazione):
        """
        Invia email di conferma prenotazione (versione sincrona per compatibilità).

        Args:
            prenotazione: Oggetto prenotazione

        Returns:
            tuple: (success, error_message)
        """
        # Per ora, restituisci sempre successo e invia in background
        # Questo evita il timeout del worker
        EmailService.send_booking_confirmation_async(prenotazione)
        return True, None

    @staticmethod
    def send_admin_pin_email(user):
        """
        Invia email con PIN di verifica per attivazione account amministratore.

        Args:
            user: Utente amministratore

        Returns:
            tuple: (success, message)
        """
        try:
            from .management.commands.send_test_pin import generate_pin  # Import local function

            # Genera PIN
            pin = generate_pin(user)

            # Preparazione messaggio specifico per admin
            base_url = settings.ALLOWED_HOSTS[0].replace('https://', '').replace('http://', '')
            full_url = f"https://{base_url}"
            subject = "Verifica email amministratore - Sistema Prenotazioni"

            message = (
                f"Ciao,\n\n"
                f"Ti è stato conferito l'accesso come amministratore del Sistema di Prenotazioni.\n\n"
                f"**URL del sito**: {full_url}\n\n"
                f"**PIN di verifica**: {pin}\n\n"
                f"Per completare l'attivazione del tuo account amministratore:\n"
                "1. Accedi al link di login nell'interfaccia web\n"
                f"2. Inserisci il codice PIN sopra quando richiesto\n\n"
                f"Una volta verificato il PIN, avrai accesso completo alle funzionalità amministrative.\n\n"
                "Se non hai richiesto questo accesso, ignora questa email.\n"
                "I PIN sono validi per 24 ore.\n\n"
                "Sistema di Prenotazioni Automatiche"
            )

            logger.info(f"=== INVIO EMAIL PIN ADMIN ===")
            logger.info(f"Destinatario: {user.email}")
            logger.info(f"PIN generato: {pin}")

            # Invia utilizzando backend SMTP robusto
            from django.core.mail.backends.smtp import EmailBackend
            from django.core.mail import EmailMessage

            backend = EmailBackend(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                timeout=15
            )

            email_message = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )

            backend.send_messages([email_message])
            backend.close()

            logger.info(f"Email PIN admin inviata con SUCCESSO a {user.email}")
            return True, "Email PIN amministratore inviata con successo"

        except Exception as e:
            error_msg = f"Errore invio email PIN amministratore: {str(e)}"
            logger.error(f"{error_msg} - Destinatario: {user.email}")
            return False, error_msg

    @staticmethod
    def test_email_configuration():
        """
        Testa la configurazione email inviando un'email di test.

        Returns:
            tuple: (success, message)
        """
        try:
            logger.info("Test configurazione email...")

            # Invia email di test all'admin
            send_mail(
                subject="Test configurazione email",
                message="Questa è un'email di test per verificare la configurazione SMTP.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False
            )

            logger.info("Email di test inviata con successo")
            return True, "Email di test inviata con successo"

        except Exception as e:
            error_msg = f"Errore configurazione email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
