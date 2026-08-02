from django.utils import timezone
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)

def get_all_notifications(user):
    today = timezone.now().date()
    notifs = {
        'factures_en_retard': [],
        'devis_expirant': [],
        'stock_bas': [],
        'locations_retard': [],
        'services_retard': [],
    }
    try:
        from apps.ventes.models import Facture
        for f in Facture.objects.filter(
            statut__in=['en_attente','partielle'],
            date_echeance__lt=today
        ).select_related('client').order_by('date_echeance')[:20]:
            jours = (today - f.date_echeance).days
            notifs['factures_en_retard'].append({
                'type': 'Facture en retard', 'icon': 'bi-receipt',
                'color': '#ef4444',
                'title': f'Facture {f.numero} — {f.client.nom}',
                'subtitle': f'{jours} jour(s) de retard — Restant : {f.montant_restant:,.2f} DA',
                'url': f'/ventes/{f.pk}/', 'date': f.date_echeance,
            })
    except Exception as e:
        logger.exception(f"Erreur dans get_all_notifications (factures en retard): {e}")
    try:
        from apps.devis.models import Devis
        for d in Devis.objects.filter(
            statut__in=['brouillon','envoye'],
            date_validite__lte=today+timedelta(days=3),
            date_validite__gte=today
        ).select_related('client')[:10]:
            jr = (d.date_validite - today).days
            notifs['devis_expirant'].append({
                'type': 'Devis expirant', 'icon': 'bi-file-text',
                'color': '#f59e0b',
                'title': f'Devis {d.numero} — {d.client.nom}',
                'subtitle': f'Expire dans {jr} jour(s)',
                'url': f'/devis/{d.pk}/', 'date': d.date_validite,
            })
    except Exception as e:
        logger.exception(f"Erreur dans get_all_notifications (devis expirant): {e}")
    try:
        from apps.produits.models import Produit
        from django.db.models import F
        for p in Produit.objects.filter(
            actif=True, supprime=False,
            quantite_stock__lte=F('seuil_alerte')
        ).order_by('quantite_stock')[:15]:
            notifs['stock_bas'].append({
                'type': 'Stock bas', 'icon': 'bi-box-seam',
                'color': '#f59e0b',
                'title': f'{p.nom} [{p.reference}]',
                'subtitle': f'Stock : {p.quantite_stock} {p.unite} (seuil : {p.seuil_alerte})',
                'url': f'/produits/{p.pk}/', 'date': None,
            })
    except Exception as e:
        logger.exception(f"Erreur dans get_all_notifications (stock bas): {e}")
    return notifs

def get_notification_count(user):
    notifs = get_all_notifications(user)
    return sum(len(v) for v in notifs.values())
