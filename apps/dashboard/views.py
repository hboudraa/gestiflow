from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone


def _previous_month(value):
    """Return the first day of the month preceding ``value``."""
    if value.month == 1:
        return date(value.year - 1, 12, 1)
    return date(value.year, value.month - 1, 1)


@login_required
def index(request):
    today = timezone.localdate()
    debut_mois = today.replace(day=1)
    fin_mois = today.replace(day=monthrange(today.year, today.month)[1])
    debut_mois_precedent = _previous_month(debut_mois)
    fin_mois_precedent = debut_mois - timezone.timedelta(days=1)
    statuts_ca = ['en_attente', 'partielle', 'payee']
    statuts_impayes = ['en_attente', 'partielle']

    from apps.clients.models import Client
    from apps.locations.models import Location
    from apps.produits.models import Produit
    from apps.services.models import OrdreDeTravail
    from apps.ventes.models import Facture

    factures_mois = Facture.objects.filter(
        date_facture__range=[debut_mois, fin_mois], statut__in=statuts_ca
    )
    ca_mois = factures_mois.aggregate(total=Sum('total_ttc'))['total'] or Decimal('0')
    ca_mois_precedent = Facture.objects.filter(
        date_facture__range=[debut_mois_precedent, fin_mois_precedent], statut__in=statuts_ca
    ).aggregate(total=Sum('total_ttc'))['total'] or Decimal('0')
    evolution_ca = (
        ((ca_mois - ca_mois_precedent) / ca_mois_precedent * Decimal('100'))
        if ca_mois_precedent else None
    )

    montant_encaisse = factures_mois.aggregate(total=Sum('montant_paye'))['total'] or Decimal('0')
    montant_impaye = Facture.objects.filter(statut__in=statuts_impayes).aggregate(
        total=Sum(ExpressionWrapper(
            F('total_ttc') - F('montant_paye'),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ))
    )['total'] or Decimal('0')
    nb_impayees = Facture.objects.filter(statut__in=statuts_impayes).count()

    # Six monthly points (including the current month), suited to a compact dashboard chart.
    first_month = debut_mois
    for _ in range(5):
        first_month = _previous_month(first_month)
    monthly_rows = Facture.objects.filter(
        date_facture__range=[first_month, fin_mois], statut__in=statuts_ca
    ).annotate(mois=TruncMonth('date_facture')).values('mois').annotate(
        total=Sum('total_ttc')
    ).order_by('mois')
    totals_by_month = {
        row['mois'].date() if hasattr(row['mois'], 'date') else row['mois']: row['total'] or Decimal('0')
        for row in monthly_rows
    }
    month_starts = []
    current_month = first_month
    for _ in range(6):
        month_starts.append(current_month)
        current_month = date(
            current_month.year + (current_month.month == 12),
            1 if current_month.month == 12 else current_month.month + 1,
            1,
        )
    max_monthly_total = max((totals_by_month.get(month, Decimal('0')) for month in month_starts), default=Decimal('0'))
    ca_evolution = [
        {
            'label': month.strftime('%b').capitalize(),
            'total': totals_by_month.get(month, Decimal('0')),
            'height': int((totals_by_month.get(month, Decimal('0')) / max_monthly_total * 100)) if max_monthly_total else 0,
        }
        for month in month_starts
    ]

    produits_actifs = Produit.objects.filter(actif=True, supprime=False)
    produits_alerte = produits_actifs.filter(quantite_stock__lte=F('seuil_alerte')).order_by('quantite_stock', 'nom')[:5]
    services_en_cours = OrdreDeTravail.objects.filter(
        statut='en_cours'
    ).select_related('client', 'technicien').order_by('-cree_le')[:5]

    ctx = {
        'aujourdhui': today,
        'ca_mois': ca_mois,
        'ca_mois_precedent': ca_mois_precedent,
        'evolution_ca': evolution_ca,
        'montant_encaisse': montant_encaisse,
        'montant_impaye': montant_impaye,
        'nb_impayees': nb_impayees,
        'nb_factures_mois': factures_mois.count(),
        'nouveaux_clients': Client.objects.filter(
            cree_le__date__range=[debut_mois, fin_mois], supprime=False
        ).count(),
        'valeur_stock': produits_actifs.aggregate(
            total=Sum(F('quantite_stock') * F('prix_achat'))
        )['total'] or Decimal('0'),
        'produits_alerte': produits_alerte,
        'nb_produits_alerte': produits_actifs.filter(quantite_stock__lte=F('seuil_alerte')).count(),
        'services_actifs': OrdreDeTravail.objects.filter(statut__in=['en_attente', 'en_cours']).count(),
        'services_en_cours': services_en_cours,
        'locations_retard': Location.objects.filter(
            statut__in=['en_cours', 'en_retard'], date_fin_prevue__lt=timezone.now()
        ).count(),
        'dernieres_factures': Facture.objects.select_related('client').order_by('-date_facture', '-cree_le')[:8],
        'ca_evolution': ca_evolution,
    }
    return render(request, 'dashboard/index.html', ctx)
