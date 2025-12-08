"""
Modulo di sicurezza per il wizard di setup.

Fornisce:
- Rate limiting per tentativi di accesso al wizard
- Logging di accessi sensibili
- Validazione delle sessioni admin
"""

import logging
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger('prenotazioni.wizard')


def check_wizard_rate_limit(request, max_attempts=5, window_minutes=15):
    """
    Rate limiting per evitare brute force sul wizard.
    
    Args:
        request: Django request object
        max_attempts: Numero massimo di tentativi
        window_minutes: Finestra temporale in minuti
    
    Returns:
        tuple (allowed: bool, remaining: int, reset_time: datetime)
    """
    # Identifica il client (IP o user_id se autenticato)
    if request.user.is_authenticated:
        client_id = f"wizard_user_{request.user.id}"
    else:
        client_id = f"wizard_ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
    
    cache_key = f"wizard_attempts_{client_id}"
    
    # Recupera tentativi correnti
    attempt_count = cache.get(cache_key, 0)
    
    if attempt_count >= max_attempts:
        # Recupera il tempo di reset
        reset_key = f"wizard_reset_{client_id}"
        reset_time = cache.get(reset_key)
        return False, 0, reset_time
    
    # Incrementa il contatore
    attempt_count += 1
    cache.set(cache_key, attempt_count, window_minutes * 60)
    
    # Se è il primo tentativo, registra il reset time
    if attempt_count == 1:
        reset_time = timezone.now() + timedelta(minutes=window_minutes)
        cache.set(f"wizard_reset_{client_id}", reset_time, window_minutes * 60)
    else:
        reset_time = cache.get(f"wizard_reset_{client_id}")
    
    remaining = max_attempts - attempt_count
    return True, remaining, reset_time


def log_wizard_access(request, action, details=None):
    """
    Registra accessi sensibili al wizard.
    
    Args:
        request: Django request object
        action: Azione eseguita (es. 'wizard_start', 'wizard_create_admin')
        details: Dict con dettagli aggiuntivi
    """
    user_info = "Anonymous"
    if request.user.is_authenticated:
        user_info = f"{request.user.username} (id={request.user.id})"
    
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')[:100]
    
    log_entry = {
        'action': action,
        'user': user_info,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'timestamp': timezone.now().isoformat(),
    }
    
    if details:
        log_entry.update(details)
    
    # Log a livello INFO per accessi sensibili, WARNING per anomalie
    if action.startswith('wizard_'):
        logger.warning(f'WIZARD_EVENT: {log_entry}')
    else:
        logger.info(f'WIZARD_LOG: {log_entry}')


def validate_wizard_admin_session(request):
    """
    Valida che l'admin nella sessione sia ancora valido e autorizzato.
    
    Returns:
        tuple (valid: bool, user: User or None, error_message: str)
    """
    # Verifica autenticazione
    if not request.user.is_authenticated:
        return False, None, "Utente non autenticato"
    
    if not request.user.is_superuser:
        return False, None, "Utente non è superuser"
    
    # Verifica che l'ID in sessione corrisponda all'utente autenticato
    admin_user_id = request.session.get('admin_user_id')
    if admin_user_id and admin_user_id != request.user.id:
        log_wizard_access(
            request,
            'wizard_session_mismatch',
            {
                'session_user_id': admin_user_id,
                'auth_user_id': request.user.id
            }
        )
        return False, None, "Sessione admin non valida (mismatch)"
    
    # Verifica che l'utente esista ancora nel DB
    try:
        user = User.objects.get(id=request.user.id)
        if not user.is_active:
            return False, None, "Account admin disattivato"
        return True, user, None
    except User.DoesNotExist:
        return False, None, "Account admin non trovato"


def check_wizard_can_proceed(request):
    """
    Verifica se il wizard può procedere (non ci sono blocchi di sicurezza).
    
    Returns:
        tuple (can_proceed: bool, error_message: str or None)
    """
    # Rate limiting
    allowed, remaining, reset_time = check_wizard_rate_limit(request)
    if not allowed:
        msg = f"Troppi tentativi. Riprova dopo {reset_time.strftime('%H:%M')}"
        log_wizard_access(request, 'wizard_rate_limit_exceeded')
        return False, msg
    
    # Session validation
    valid, user, error = validate_wizard_admin_session(request)
    if not valid:
        return False, error
    
    return True, None


def log_wizard_step_completion(request, step, success=True, error_msg=None):
    """
    Registra il completamento di uno step del wizard.
    
    Args:
        request: Django request object
        step: Nome dello step (es. 'admin', 'school', 'device')
        success: True se completato con successo
        error_msg: Messaggio di errore se success=False
    """
    action = f"wizard_step_{'success' if success else 'error'}_{step}"
    details = {
        'step': step,
        'success': success,
    }
    
    if error_msg:
        details['error'] = error_msg
    
    log_wizard_access(request, action, details)
