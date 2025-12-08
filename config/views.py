from django.shortcuts import render, redirect
from django.http import HttpResponse
import logging

def home(request):
    """
    Home page - sempre accessibile.
    Se il sistema non è configurato, mostra un messaggio all'utente.
    """
    try:
        from prenotazioni.models import Risorsa, ConfigurazioneSistema
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Controlla se il setup è completato usando il flag nel DB
        setup_flag = ConfigurazioneSistema.ottieni_configurazione('SETUP_COMPLETED', default=None)
        
        # Se l'utente è un superuser E il setup non è completato,
        # mostra un messaggio invitandolo ad andare al setup
        context = {
            'setup_needed': setup_flag is None and User.objects.filter(is_superuser=True).exists(),
            'is_admin': request.user.is_superuser if request.user.is_authenticated else False,
        }
        
        return render(request, 'home.html', context)
    except Exception:
        logging.getLogger('prenotazioni').exception('Error while checking initial setup in home view')
        # Se le tabelle non esistono, mostra comunque la home
        return render(request, 'home.html', {'setup_needed': False, 'is_admin': False})

def health_check(request):
    """Health check endpoint for Render deployment monitoring"""
    try:
        # Test database connection using Django ORM
        from django.contrib.auth import get_user_model
        User = get_user_model()
        User.objects.count()
        return HttpResponse("OK", status=200)
    except Exception as e:
        return HttpResponse(f"Database Error: {str(e)}", status=500)
