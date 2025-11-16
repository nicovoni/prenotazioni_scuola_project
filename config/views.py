from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection

def home(request):
    # Controllo se il sistema è configurato
    from prenotazioni.models import Utente, Risorsa
    if not Utente.objects.exists() or not Risorsa.objects.exists():
        return redirect('prenotazioni:configurazione_sistema')
    return render(request, 'home.html')

def health_check(request):
    """Health check endpoint for Render deployment monitoring"""
    try:
        # Test database connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return HttpResponse("OK", status=200)
    except Exception as e:
        return HttpResponse("Database Error", status=500)
