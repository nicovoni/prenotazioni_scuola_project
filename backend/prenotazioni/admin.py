from django.contrib import admin
from .models import Utente,Risorsa,Prenotazione
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.conf import settings

@admin.register(Utente)
class UtenteAdmin(BaseUserAdmin):
    fieldsets=BaseUserAdmin.fieldsets+(('Ruolo',{'fields':('ruolo',)}),)

@admin.register(Risorsa)
class RisorsaAdmin(admin.ModelAdmin):
    list_display=('nome','tipo','quantita_totale')

@admin.register(Prenotazione)
class PrenotazioneAdmin(admin.ModelAdmin):
    list_display=('risorsa','utente','inizio','fine')

admin.site.site_header=settings.SCHOOL_NAME+' - '+settings.AUTHOR
