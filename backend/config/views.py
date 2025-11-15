from django.shortcuts import render, redirect

def home(request):
    # Controllo se il sistema è configurato
    from prenotazioni.models import Utente, Risorsa
    if not Utente.objects.exists() or not Risorsa.objects.exists():
        return redirect('configurazione_sistema')
    return render(request, 'home.html')
