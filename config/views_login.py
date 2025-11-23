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
            login(request, user)
            # Se non esistono admin e risorse, redirect a configurazione iniziale
            if not User.objects.filter(is_superuser=True).exists() and Risorsa.objects.count() == 0:
                return redirect('/api/setup/')
            return redirect('home')
        else:
            messages.error(request, "Credenziali non valide. Riprova.")
    return render(request, 'registration/login.html')
