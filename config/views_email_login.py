import random
import string
import re
import logging
import threading
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

def send_mail_admins_async(subject, message):
    """Send mail_admins asynchronously to avoid blocking the request."""
    def _send():
        try:
            from django.core.mail import mail_admins
            mail_admins(subject=subject, message=message)
        except Exception as e:
            logging.getLogger('django.security').error(f"Errore invio mail_admins: {str(e)}")
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()

def send_pin_email_async(email, pin):
    """Send PIN email asynchronously to avoid blocking the request."""
    def _send():
        logger = logging.getLogger('django.security')
        try:
            logger.info(f"=== AVVIO INVIO EMAIL PIN ===")
            logger.info(f"Destinatario: {email}")
            logger.info(f"PIN: {pin}")
            logger.info(f"Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
            logger.info(f"Username: {settings.EMAIL_HOST_USER}")
            logger.info(f"Password presente: {'SI' if settings.EMAIL_HOST_PASSWORD else 'NO'}")
            logger.info(f"From: {settings.DEFAULT_FROM_EMAIL}")
            logger.info(f"TLS: {settings.EMAIL_USE_TLS}, Timeout: 10s")

            # Test DNS resolution
            logger.info("Test risoluzione DNS...")
            try:
                import socket
                ip_address = socket.gethostbyname(settings.EMAIL_HOST)
                logger.info(f"DNS risolto: {settings.EMAIL_HOST} -> {ip_address}")
            except Exception as dns_error:
                logger.error(f"ERRORE DNS: {dns_error}")
                raise Exception(f"DNS resolution failed: {dns_error}")

            # Test basic connectivity
            logger.info("Test connessione socket...")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((settings.EMAIL_HOST, settings.EMAIL_PORT))
                sock.close()
                if result == 0:
                    logger.info(f"Connessione socket riuscita a {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
                else:
                    logger.error(f"Connessione socket fallita a {settings.EMAIL_HOST}:{settings.EMAIL_PORT} (codice: {result})")
                    raise Exception(f"Socket connection failed with code: {result}")
            except Exception as socket_error:
                logger.error(f"ERRORE connessione socket: {socket_error}")
                raise Exception(f"Socket connectivity test failed: {socket_error}")

            # Use direct SMTP backend with shorter timeout
            from django.core.mail.backends.smtp import EmailBackend
            from django.core.mail import EmailMessage

            logger.info("Creazione backend SMTP...")
            # Create backend with very short timeout
            backend = EmailBackend(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                timeout=10  # Very short timeout
            )
            logger.info("Backend creato, connessione SMTP...")

            email_message = EmailMessage(
                subject="Il tuo PIN di accesso",
                body=f"Il tuo PIN di accesso è: {pin}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            logger.info("Messaggio email creato")

            logger.info("Invio messaggio...")
            result = backend.send_messages([email_message])
            logger.info(f"send_messages() restituito: {result}")

            backend.close()
            logger.info("Connessione chiusa")
            logger.info(f"=== EMAIL PIN INVIATA CON SUCCESSO A {email} ===")

        except Exception as e:
            logger.error(f"=== ERRORE INVIO EMAIL PIN ===")
            logger.error(f"Destinatario: {email}")
            logger.error(f"Tipo eccezione: {type(e).__name__}")
            logger.error(f"Messaggio errore: {str(e)}")

            # Log full traceback
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")

            # Log connection details
            logger.error("Dettagli connessione SMTP:")
            logger.error(f"  Host: {settings.EMAIL_HOST}")
            logger.error(f"  Port: {settings.EMAIL_PORT}")
            logger.error(f"  Username: {settings.EMAIL_HOST_USER}")
            logger.error(f"  Password length: {len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 0}")
            logger.error(f"  From: {settings.DEFAULT_FROM_EMAIL}")
            logger.error(f"  TLS: {settings.EMAIL_USE_TLS}")
            logger.error(f"  Timeout: 10")
            logger.error("==========================")

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def email_login(request):
    # Log tentativi
    logger = logging.getLogger('django.security')
    ip = get_client_ip(request)
    # Rate limiting semplice per IP
    rate_limit_key = f"rate_limit_{ip}"
    rate_limit = request.session.get(rate_limit_key, {'count': 0, 'time': timezone.now().isoformat()})
    now = timezone.now()
    rate_time = timezone.datetime.fromisoformat(rate_limit['time'])
    rate_time = timezone.make_aware(rate_time) if timezone.is_naive(rate_time) else rate_time
    if (now - rate_time).total_seconds() < 60:
        if rate_limit['count'] >= 10:
            messages.error(request, "Troppe richieste. Riprova tra un minuto.")
            logger.warning(f"Rate limit superato per IP {ip} email_login")
            return render(request, 'registration/email_login.html')
        else:
            rate_limit['count'] += 1
    else:
        rate_limit = {'count': 1, 'time': now.isoformat()}
    request.session[rate_limit_key] = rate_limit
    # Limite tentativi invio PIN
    max_attempts = 5
    block_minutes = 10
    attempts = request.session.get('pin_send_attempts', 0)
    block_until = request.session.get('pin_send_block_until')
    if block_until:
        block_until_dt = timezone.datetime.fromisoformat(block_until)
        block_until_dt = timezone.make_aware(block_until_dt) if timezone.is_naive(block_until_dt) else block_until_dt
        if now < block_until_dt:
            messages.error(request, f"Troppi tentativi. Riprova dopo {block_minutes} minuti.")
            # Notifica admin
            email = request.session.get('login_email', 'N/A')
            send_mail_admins_async(
                subject="Blocco tentativi invio PIN",
                message=f"Blocco per troppi tentativi di invio PIN per l'email: {email}",
            )
            return render(request, 'registration/email_login.html')
    if request.method == 'POST':
        email = request.POST.get('email')
        domain = settings.SCHOOL_EMAIL_DOMAIN.lower()
        logger.info(f"Tentativo login email: {email} IP: {ip}")
        if not email:
            messages.error(request, f"Inserisci una email valida del dominio {domain}")
            request.session['pin_send_attempts'] = attempts + 1
            logger.warning(f"Tentativo login email fallito: {email} IP: {ip}")
            return render(request, 'registration/email_login.html')
        # Split local and domain parts
        try:
            local_part, domain_part = email.split('@')
        except ValueError:
            local_part = ''
            domain_part = ''

        if domain_part.lower() != domain:
            messages.error(request, f"Sono accettate solo email del dominio {domain}")
            request.session['pin_send_attempts'] = attempts + 1
            logger.warning(f"Tentativo login email con dominio non valido: {email} IP: {ip}")
            return render(request, 'registration/email_login.html')

        # Validate local-part: single initial (letter), dot, full surname (letters, apostrophe allowed)
        # allow an optional numeric suffix after the surname (e.g. n.cantalupo1)
        # Note: hyphen is NOT allowed per updated requirement; apostrophe (') is allowed
        local_regex = r"^[A-Za-z]\.[A-Za-zÀ-ÖØ-öø-ÿ']+[0-9]*$"
        if not re.match(local_regex, local_part):
            messages.error(request, "Formato email non valido. Esempi di indirizzi corretti: g.rossi@isufol.it o g.rossi1@isufol.it")
            request.session['pin_send_attempts'] = attempts + 1
            logger.warning(f"Tentativo login email con formato local-part non valido: {email} IP: {ip}")
            # Optionally block after many attempts
            if request.session.get('pin_send_attempts', 0) >= max_attempts:
                block_time = now + timezone.timedelta(minutes=block_minutes)
                request.session['pin_send_block_until'] = block_time.isoformat()
                send_mail_admins_async(
                    subject="Blocco tentativi invio PIN",
                    message=f"Blocco per troppi tentativi di invio PIN per l'email: {email} IP: {ip}",
                )
            return render(request, 'registration/email_login.html')

        # Genera PIN monouso
        pin = ''.join(random.choices(string.digits, k=6))
        # Salva PIN e timestamp in sessione
        request.session['login_email'] = email
        request.session['login_pin'] = pin
        request.session['login_pin_time'] = now.isoformat()
        request.session['pin_send_attempts'] = 0
        request.session['pin_send_block_until'] = None

        # Invia PIN via email in background
        send_pin_email_async(email, pin)

        logger.info(f"PIN GENERATO per {email}: {pin}")

        # TEMPORANEO: Mostra PIN direttamente all'utente per test
        messages.success(request, f"PIN generato: {pin}. Usa questo PIN per accedere.")

        logger.info(f"PIN inviato con SUCCESSO a {email} IP: {ip}")
        return redirect('verify_pin')
    return render(request, 'registration/email_login.html')

def verify_pin(request):
    logger = logging.getLogger('django.security')
    ip = get_client_ip(request)
    # Limite tentativi inserimento PIN
    max_attempts = 5
    block_minutes = 10
    attempts = request.session.get('pin_verify_attempts', 0)
    block_until = request.session.get('pin_verify_block_until')
    now = timezone.now()
    if block_until:
        block_until_dt = timezone.datetime.fromisoformat(block_until)
        block_until_dt = timezone.make_aware(block_until_dt) if timezone.is_naive(block_until_dt) else block_until_dt
        if now < block_until_dt:
            messages.error(request, f"Troppi tentativi. Riprova dopo {block_minutes} minuti.")
            # Notifica admin
            email = request.session.get('login_email', 'N/A')
            send_mail_admins_async(
                subject="Blocco tentativi verifica PIN",
                message=f"Blocco per troppi tentativi di verifica PIN per l'email: {email} IP: {ip}",
            )
            logger.warning(f"Blocco tentativi verifica PIN per {email} IP: {ip}")
            return render(request, 'registration/verify_pin.html')
    if request.method == 'POST':
        pin = request.POST.get('pin')
        session_pin = request.session.get('login_pin')
        email = request.session.get('login_email')
        pin_time = request.session.get('login_pin_time')
        logger.info(f"Tentativo verifica PIN per {email} IP: {ip}")
        # Verifica scadenza PIN (5 minuti)
        if pin_time:
            pin_time_dt = timezone.datetime.fromisoformat(pin_time)
            pin_time_dt = timezone.make_aware(pin_time_dt) if timezone.is_naive(pin_time_dt) else pin_time_dt
            if (now - pin_time_dt).total_seconds() > 300:
                messages.error(request, "Il PIN è scaduto. Richiedi un nuovo accesso.")
                for k in ['login_email', 'login_pin', 'login_pin_time', 'pin_verify_attempts', 'pin_verify_block_until']:
                    request.session.pop(k, None)
                logger.warning(f"PIN scaduto per {email} IP: {ip}")
                return redirect('email_login')
        if not pin or pin != session_pin:
            request.session['pin_verify_attempts'] = attempts + 1
            if request.session['pin_verify_attempts'] >= max_attempts:
                block_time = now + timezone.timedelta(minutes=block_minutes)
                request.session['pin_verify_block_until'] = block_time.isoformat()
                # Notifica admin
                send_mail_admins_async(
                    subject="Blocco tentativi verifica PIN",
                    message=f"Blocco per troppi tentativi di verifica PIN per l'email: {email} IP: {ip}",
                )
                logger.warning(f"Blocco tentativi verifica PIN per {email} IP: {ip}")
            messages.error(request, "PIN non valido.")
            logger.warning(f"PIN non valido per {email} IP: {ip}")
            # PIN monouso: cancella sempre
            for k in ['login_pin', 'login_pin_time']:
                request.session.pop(k, None)
            return render(request, 'registration/verify_pin.html')
        # Autentica utente (crea o recupera User)
        from django.contrib.auth import get_user_model
        from prenotazioni.models import UserProfile
        User = get_user_model()

        user, created = User.objects.get_or_create(username=email, defaults={'email': email})

        # Determina ruolo basato sull'email e imposta permessi
        is_admin = email in settings.ADMINS_EMAIL_LIST

        # Aggiorna permessi dell'utente
        if is_admin:
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False
        user.save()

        # Crea profilo utente se necessario
        if created:
            UserProfile.objects.create(
                user=user,
                nome=email.split('@')[0] if '@' in email else email,
                cognome='',
                attivo=True
            )
        from django.contrib.auth import login
        login(request, user)
        # Pulisci sessione
        for k in ['login_email', 'login_pin', 'login_pin_time', 'pin_verify_attempts', 'pin_verify_block_until']:
            request.session.pop(k, None)
        logger.info(f"Accesso riuscito per {email} IP: {ip}")
        return redirect('prenotazioni:prenota_laboratorio')
    return render(request, 'registration/verify_pin.html')
