"""
Servizi per la logica di business delle prenotazioni.
Estraggono la logica complessa dalle views per migliorare manutenibilità.
"""
import logging
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
            try:
                EmailService.send_booking_confirmation(prenotazione)
            except Exception as e:
                logger.warning(f"Errore invio email conferma: {e}")

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
            utente: Utente proprietario
            inizio: Nuovo inizio
            fine: Nuova fine
            quantita: Nuova quantità

        Returns:
            tuple: (success, prenotazione_or_errors)
        """
        try:
            prenotazione = Prenotazione.objects.get(pk=prenotazione_id)

            if prenotazione.utente != utente:
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
            utente: Utente proprietario

        Returns:
            tuple: (success, errors)
        """
        try:
            prenotazione = Prenotazione.objects.get(pk=prenotazione_id)

            if prenotazione.utente != utente:
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
    def send_booking_confirmation(prenotazione):
        """
        Invia email di conferma prenotazione.

        Args:
            prenotazione: Oggetto prenotazione
        """
        subject = f"Conferma prenotazione: {prenotazione.risorsa.nome}"
        message = (
            f"Ciao {prenotazione.utente.first_name or prenotazione.utente.username},\n\n"
            f"La tua prenotazione per {prenotazione.risorsa.nome} è stata confermata.\n"
            f"Data: {prenotazione.inizio.date()}\n"
            f"Orario: {prenotazione.inizio.time().strftime('%H:%M')} - {prenotazione.fine.time().strftime('%H:%M')}\n"
            f"Quantità: {prenotazione.quantita}\n\n"
            "Grazie per aver utilizzato il sistema di prenotazioni. Buona giornata!"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[prenotazione.utente.email],
            fail_silently=True
        )

        logger.info(f"Email conferma inviata per prenotazione {prenotazione.id}")
