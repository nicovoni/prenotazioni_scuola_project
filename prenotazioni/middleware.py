from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404
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
        # Also accept API-prefixed account paths to avoid redirect loops when
        # the app is mounted under an '/api/' prefix (e.g. /api/accounts/password_change/).
        '/api/accounts/password_change/',
        '/api/accounts/password_change/done/',
        '/api/accounts/login/',
        '/api/accounts/logout/',
    ]

    # Exempt by view name (namespace-aware). Using resolve() is more robust
    # than path matching because the app might be mounted under prefixes.
    EXEMPT_VIEW_LOCAL_NAMES = {'password_change', 'password_change_done', 'login', 'logout'}
    EXEMPT_VIEW_FULL_NAMES = {'prenotazioni:password_change', 'prenotazioni:password_change_done', 'login', 'logout'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        path = request.path

        # First, try to resolve the path to a view name and exempt known
        # view names. This is robust when the app is mounted under a prefix
        # like '/api/'. If resolve fails, fall back to path matching.
        try:
            match = resolve(request.path_info)
            view_name = match.view_name or ''
            # Direct full-name match (namespace:name)
            if view_name in self.EXEMPT_VIEW_FULL_NAMES:
                return self.get_response(request)
            # Local name match (ignore namespace)
            if view_name and view_name.split(':')[-1] in self.EXEMPT_VIEW_LOCAL_NAMES:
                return self.get_response(request)
        except Resolver404:
            # Could not resolve — fall back to path checks below
            pass

        # Fallback: allow exempt paths. Use startswith/containment so paths
        # mounted under prefixes are still recognized as exempt.
        for p in self.EXEMPT_PATHS:
            try:
                if path.startswith(p) or p in path:
                    return self.get_response(request)
            except Exception:
                continue

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
