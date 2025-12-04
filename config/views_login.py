import os
from django.contrib.auth import authenticate, login, get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages
from prenotazioni.models import Risorsa
User = get_user_model()

def custom_login(request):
    # Redirect GET requests to the email-based PIN login page (single email field)
    if request.method == 'GET':
        return redirect('email_login')
    # If someone POSTs username/password here, keep legacy behavior (allow admin login via standard auth)
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
                            'cognome_utente': 'Amministratore'
                        }
                    )
                    profil.must_change_password = True
                    profil.password_last_changed = None
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
            if not User.objects.filter(is_superuser=True).exists() and Risorsa.objects.count() == 0:
                from django.urls import reverse
                return redirect(reverse('prenotazioni:setup_amministratore'))
            return redirect('home')
        else:
            messages.error(request, "Credenziali non valide. Riprova.")
    return render(request, 'registration/login.html')
