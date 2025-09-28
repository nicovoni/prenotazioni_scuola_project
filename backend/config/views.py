from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>Benvenuto nel sistema di prenotazioni della scuola!</h1>")
