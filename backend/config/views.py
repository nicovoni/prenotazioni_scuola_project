from django.shortcuts import render, redirect

def home(request):
    # Controllo se il sistema è configurato
    from prenotazioni.models import Risorsa
    from django.contrib.auth.models import User
    if not User.objects.exists() or not Risorsa.objects.exists():
        return redirect('configurazione_sistema')
    return render(request, 'home.html')
