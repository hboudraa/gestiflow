import logging
logger = logging.getLogger(__name__)

class SecurityEvent:
    LOGIN_SUCCESS = 'LOGIN_OK'
    LOGIN_FAILED  = 'LOGIN_FAIL'
    LOGIN_BLOCKED = 'LOGIN_BLOCKED'
    LOGOUT        = 'LOGOUT'
    ACCESS_DENIED = 'ACCESS_DENIED'
    DATA_EXPORT   = 'DATA_EXPORT'
    SETTINGS_CHANGED = 'SETTINGS_CHANGED'

def log_security_event(event_type, request=None, utilisateur=None, details='', module='Securite'):
    try:
        from apps.core.models import LogActivite
        ip = ''
        if request:
            xff = request.META.get('HTTP_X_FORWARDED_FOR')
            ip  = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR','')
            if utilisateur is None and request.user.is_authenticated:
                utilisateur = request.user
        LogActivite.objects.create(
            utilisateur=utilisateur, action=event_type,
            module=module, details=details[:500], adresse_ip=ip or None,
        )
    except Exception as e:
        logger.exception(f"Erreur dans log_security_event: {e}")

def log_login_success(request, user):
    log_security_event(SecurityEvent.LOGIN_SUCCESS, request, user, f'Connexion — {user.username}')

def log_login_failed(request, username):
    log_security_event(SecurityEvent.LOGIN_FAILED, request, details=f'Echec — {username[:50]}')

def log_logout(request):
    log_security_event(SecurityEvent.LOGOUT, request, details='Deconnexion')
