from django.shortcuts import render, redirect
from django.http import HttpResponse
import logging

def home(request):
    # Controllo se il sistema è configurato
    try:
        from prenotazioni.models import Risorsa
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.exists() or not Risorsa.objects.exists():
            return redirect('prenotazioni:configurazione_sistema')
        return render(request, 'home.html')
    except Exception:
        logging.getLogger('prenotazioni').exception('Error while checking initial setup in home view')
        # Se le tabelle non esistono, redirect alla configurazione
        # Questo permette al sito di funzionare durante il deploy
        return redirect('prenotazioni:configurazione_sistema')

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
