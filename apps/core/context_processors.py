from django.conf import settings as dj_settings
import logging
logger = logging.getLogger(__name__)

def _get_entreprise():
    base = getattr(dj_settings, 'GESTIFLOW', {})
    try:
        from apps.core.models import Parametre
        return {
            'NOM_ENTREPRISE': Parametre.get('NOM_ENTREPRISE', base.get('NOM_ENTREPRISE', 'Mon Entreprise')),
            'ADRESSE':   Parametre.get('ADRESSE',   base.get('ADRESSE',   '')),
            'TELEPHONE': Parametre.get('TELEPHONE', base.get('TELEPHONE', '')),
            'EMAIL':     Parametre.get('EMAIL',     base.get('EMAIL',     '')),
            'DEVISE':    Parametre.get('DEVISE',    base.get('DEVISE',    'DA')),
            'TVA_DEFAUT':Parametre.get('TVA_DEFAUT',base.get('TVA_DEFAUT','19')),
            'LOGO':      Parametre.get('LOGO',      ''),
        }
    except Exception as e:
        logger.exception(f"Erreur dans _get_entreprise: {e}")
        return base

def global_context(request):
    ctx = {'ENTREPRISE': _get_entreprise(), 'APP_VERSION': '1.0.0'}
    if request.user.is_authenticated:
        try:
            from apps.core.notifications import get_notification_count
            ctx['notifications_count'] = get_notification_count(request.user)
        except Exception as e:
            logger.exception(f"Erreur dans global_context (notifications): {e}")
            ctx['notifications_count'] = 0
        try:
            from apps.produits.models import Produit
            from django.db.models import F
            ctx['alertes_stock_count'] = Produit.objects.filter(
                quantite_stock__lte=F('seuil_alerte'), actif=True, supprime=False
            ).count()
        except Exception as e:
            logger.exception(f"Erreur dans global_context (alertes stock): {e}")
            ctx['alertes_stock_count'] = 0
    return ctx
