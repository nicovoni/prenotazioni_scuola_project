from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import Utente, Risorsa, Prenotazione

# Admin per Utente personalizzato
@admin.register(Utente)
class UtenteAdmin(UserAdmin):
    model = Utente
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'telefono', 'classe')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'ruolo')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'ruolo'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'ruolo', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

# Admin per Risorsa
@admin.register(Risorsa)
class RisorsaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'capacita_massima', 'attiva')
    list_filter = ('tipo',)
    search_fields = ('nome',)

# Admin per Prenotazione
@admin.register(Prenotazione)
class PrenotazioneAdmin(admin.ModelAdmin):
    list_display = ('utente', 'risorsa', 'quantita', 'inizio', 'fine')
    list_filter = ('risorsa', 'inizio', 'fine')
    search_fields = ('utente__username', 'risorsa__nome')

# Branding dell'admin
admin.site.site_header = f"{settings.SCHOOL_NAME} - {settings.AUTHOR}"
