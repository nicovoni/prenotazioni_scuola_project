
from rest_framework import routers
from .views import BookingViewSet, prenota_laboratorio, lista_prenotazioni, edit_prenotazione, delete_prenotazione, database_viewer, configurazione_sistema, admin_operazioni, setup_amministratore
from django.urls import path, include
from ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test

app_name = 'prenotazioni'

router = routers.DefaultRouter()
router.register(r'prenotazioni', BookingViewSet)

# Decoratori di sicurezza per view sensibili
admin_required = user_passes_test(lambda u: u.is_staff)

urlpatterns = [
    path('prenota/', login_required(ratelimit(key='user', rate='10/m', block=True)(prenota_laboratorio)), name='prenota_laboratorio'),
    path('mie-prenotazioni/', login_required(ratelimit(key='user', rate='10/m', block=True)(lista_prenotazioni)), name='lista_prenotazioni'),
    path('prenotazione/<int:pk>/edit/', login_required(ratelimit(key='user', rate='10/m', block=True)(edit_prenotazione)), name='edit_prenotazione'),
    path('prenotazione/<int:pk>/delete/', login_required(ratelimit(key='user', rate='10/m', block=True)(delete_prenotazione)), name='delete_prenotazione'),
    path('database-viewer/', login_required(admin_required(ratelimit(key='user', rate='5/m', block=True)(database_viewer))), name='database_viewer'),
    path('configurazione-sistema/', login_required(admin_required(ratelimit(key='user', rate='5/m', block=True)(configurazione_sistema))), name='configurazione_sistema'),
    path('admin-operazioni/', login_required(admin_required(ratelimit(key='user', rate='5/m', block=True)(admin_operazioni))), name='admin_operazioni'),
    path('setup/', ratelimit(key='ip', rate='5/m', block=True)(setup_amministratore), name='setup_amministratore'),
    path('', include(router.urls)),
]
