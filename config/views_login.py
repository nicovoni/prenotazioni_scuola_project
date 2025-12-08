import os
from django.contrib.auth import authenticate, login, get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages
from prenotazioni.models import Risorsa
from urllib.parse import urlparse
User = get_user_model()

def custom_login(request):
    # Redirect GET requests to the email-based PIN login page (single email field)
    if request.method == 'GET':
        # If the setup wizard state is present in session, prefer redirecting
        # to the setup page so that an admin who is mid-wizard can resume.
        # Note: the setup page no longer embeds an inline login — administrators
        # should authenticate through the dedicated admin login page (`login_admin`).
        try:
            if request.session.get('wizard_in_progress'):
                from django.urls import reverse
                return redirect(reverse('prenotazioni:setup_amministratore'))
        except Exception:
            pass
        return redirect('email_login')
    # If someone POSTs username/password here, keep legacy behavior (allow admin login via standard auth)
    def _get_internal_referer():
        """Return a safe internal path extracted from HTTP_REFERER, or None."""
        referer = request.META.get('HTTP_REFERER')
        if not referer:
            return None
        try:
            parsed = urlparse(referer)
            # allow relative paths or same-host absolute URLs
            host = request.get_host()
            if (not parsed.netloc) or parsed.netloc == host:
                return parsed.path or '/'
        except Exception:
            return None
        return None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email_domain = os.environ.get('SCHOOL_EMAIL_DOMAIN', 'isufol.it')
        # Consenti login solo se username è una email con dominio autorizzato
        if username and '@' in username:
            user_domain = username.split('@')[-1].lower()
            if user_domain != email_domain.lower():
                messages.error(request, f"Accesso consentito solo per email del dominio {email_domain}")
                return render(request, 'registration/login.html')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # If setup flag is not present, and a superuser logged in, mark this
            # session as the wizard admin and force password change so the setup
            # wizard can continue (covers admins created outside the wizard).
            try:
                from prenotazioni.models import ConfigurazioneSistema, ProfiloUtente
                setup_completed = ConfigurazioneSistema.ottieni_configurazione('SETUP_COMPLETED', default=None)
            except Exception:
                setup_completed = None

            if not setup_completed and getattr(user, 'is_superuser', False):
                try:
                    # ensure profile exists and force password change
                    profil, created = ProfiloUtente.objects.get_or_create(
                        utente=user,
                        defaults={
                            'nome_utente': user.username, 
                            'cognome_utente': 'Amministratore',
                            'first_login': True
                        }
                    )
                    # Se il profilo è nuovo, impostiamo il flag
                    if created:
                        profil.must_change_password = True
                        profil.password_last_changed = None
                        profil.first_login = True
                        profil.save()
                    # mark this session to indicate the wizard should continue
                    request.session['wizard_in_progress'] = True
                    request.session['admin_user_id'] = user.id
                    request.session.save()
                except Exception:
                    pass

            # If wizard created a default admin and we're in the wizard flow,
            # ensure the user's profile exists and that the password change is enforced.
            try:
                wizard_in_progress = request.session.get('wizard_in_progress')
            except Exception:
                wizard_in_progress = False

            if wizard_in_progress and getattr(user, 'is_superuser', False):
                try:
                    from prenotazioni.models import ProfiloUtente
                    profil, created = ProfiloUtente.objects.get_or_create(
                        utente=user,
                        defaults={
                            'nome_utente': user.username,
                            'cognome_utente': 'Amministratore',
                            'first_login': True
                        }
                    )
                    # Se il profilo è nuovo, impostiamo i flag di force change password
                    if created:
                        profil.must_change_password = True
                        profil.password_last_changed = None
                        profil.first_login = True
                        profil.save()
                except Exception:
                    # If profile creation fails, continue — we still attempt login
                    pass

            login(request, user)
            # If we're in the wizard flow, handle continuation after password change
            try:
                wizard_in_progress = request.session.get('wizard_in_progress')
                password_changed = request.session.get('wizard_password_changed')
            except Exception:
                wizard_in_progress = False
                password_changed = False

            if wizard_in_progress and password_changed:
                # finalize wizard: mark admin_user in session and continue to setup
                try:
                    request.session['admin_user_id'] = user.id
                    # clear temporary flags
                    request.session.pop('wizard_password_changed', None)
                    request.session.pop('wizard_admin_password', None)
                    request.session.pop('wizard_in_progress', None)
                    request.session.save()
                except Exception:
                    pass
                from django.urls import reverse
                return redirect(reverse('prenotazioni:setup_amministratore'))

            # If wizard is in progress and the user is superuser, but password hasn't been
            # changed yet, redirect them to the forced password change page immediately.
            try:
                    if wizard_in_progress and getattr(user, 'is_superuser', False) and not request.session.get('wizard_password_changed'):
                        from django.urls import reverse
                        return redirect(reverse('prenotazioni:password_change'))
            except Exception:
                pass

            # Se non esistono admin e risorse, redirect a configurazione iniziale
            # If no special wizard flow, prefer redirecting back to the referer
            # page if it is internal, otherwise default to home.
            try:
                ref = _get_internal_referer()
                if ref:
                    return redirect(ref)
            except Exception:
                pass
            if not User.objects.filter(is_superuser=True).exists() and Risorsa.objects.count() == 0:
                from django.urls import reverse
                return redirect(reverse('prenotazioni:setup_amministratore'))
            return redirect('home')
        else:
            messages.error(request, "Credenziali non valide. Riprova.")
            # If POST originated from an internal page (e.g. setup or admin-login),
            # prefer returning the user there instead of sending them to the
            # email+PIN flow.
            try:
                ref = _get_internal_referer()
                if ref:
                    return redirect(ref)
            except Exception:
                pass
            # If this session is running the setup wizard, send the user back
            # to the setup page rather than the email-based login screen.
            try:
                if request.session.get('wizard_in_progress'):
                    from django.urls import reverse
                    return redirect(reverse('prenotazioni:setup_amministratore'))
            except Exception:
                pass
    return render(request, 'registration/login.html')


def admin_login_view(request):
    """Render a simple username/password form for administrators.

    The form posts to the shared `custom_login` handler which authenticates
    and performs wizard continuation logic.
    
    Rate limiting is applied here to prevent brute force attacks on admin accounts.
    """
    from prenotazioni.wizard_security import check_wizard_rate_limit
    from django.contrib import messages
    
    # Rate limiting per il login admin
    allowed, remaining, reset_time = check_wizard_rate_limit(request)
    if not allowed and reset_time:
        messages.error(
            request,
            f'⚠️  Troppi tentativi di accesso. Riprova dopo {reset_time.strftime("%H:%M")}'
        )
        return render(request, 'registration/login_admin.html', {
            'rate_limited': True,
            'reset_time': reset_time
        })
    
    # If the session is running the wizard, prefer showing the setup page
    try:
        if request.session.get('wizard_in_progress'):
            from django.urls import reverse
            return redirect(reverse('prenotazioni:setup_amministratore'))
    except Exception:
        pass
    if request.method == 'GET':
        return render(request, 'registration/login_admin.html')
    # For POST, delegate to custom_login for consistent behavior
    return custom_login(request)


def teacher_login_view(request):
    """Render the teacher/email login entrypoint.

    This either redirects to the existing email-login flow or renders its
    template directly, keeping behavior unchanged.
    """
    if request.method == 'GET':
        return redirect('email_login')
    return custom_login(request)
