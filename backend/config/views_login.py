import os
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

def custom_login(request):
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
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            messages.error(request, "Credenziali non valide. Riprova.")
    return render(request, 'registration/login.html')
