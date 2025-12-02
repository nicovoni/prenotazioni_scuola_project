from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

class ForcePasswordChangeMiddleware:
    """Middleware che forza il cambio password per superuser con flag must_change_password

    Regole:
    - Se l'utente è autenticato, è superuser e `profilo_utente.must_change_password` è True,
      allora reindirizza alla pagina di cambio password.
    - Ignora il path del logout, login, password change e gli endpoint API di sanity/debug.
    """
    EXEMPT_PATHS = [
        '/accounts/password_change/',
        '/accounts/password_change/done/',
        '/accounts/login/',
        '/accounts/logout/',
        '/api/debug/sanity/',
        '/api/debug/devices/',
        '/api/debug/devices/create_test/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        path = request.path

        # Allow exempt paths
        for p in self.EXEMPT_PATHS:
            if path.startswith(p):
                return self.get_response(request)

        try:
            if user and user.is_authenticated and user.is_superuser:
                profil = getattr(user, 'profilo_utente', None)
                if profil:
                    # Check expiry: if password_last_changed older than settings.PASSWORD_MAX_AGE_DAYS
                    from django.conf import settings
                    max_days = getattr(settings, 'PASSWORD_MAX_AGE_DAYS', 100)
                    if profil.password_last_changed:
                        delta = timezone.now() - profil.password_last_changed
                        if delta.days >= max_days:
                            profil.must_change_password = True
                            profil.save()

                    if profil.must_change_password:
                        # redirect to password change page
                        return redirect(reverse('prenotazioni:password_change'))
        except Exception:
            # silent fail — do not break site
            pass

        return self.get_response(request)
