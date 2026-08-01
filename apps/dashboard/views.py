from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Q, F

@login_required
def index(request):
    today = timezone.now().date()
    ctx   = {}
    try:
        from apps.ventes.models import Facture
        ctx['ca_mois']        = Facture.objects.filter(date_facture__month=today.month, date_facture__year=today.year, statut__in=['en_attente','partielle','payee']).aggregate(t=Sum('total_ttc'))['t'] or 0
        ctx['montant_encaisse']= Facture.objects.filter(date_facture__month=today.month, date_facture__year=today.year).aggregate(t=Sum('montant_paye'))['t'] or 0
        ctx['factures_impayees']= Facture.objects.filter(statut__in=['en_attente','partielle']).aggregate(t=Sum('total_ttc'))['t'] or 0
        ctx['nb_impayees']     = Facture.objects.filter(statut__in=['en_attente','partielle']).count()
        ctx['dernieres_factures'] = Facture.objects.select_related('client').order_by('-date_facture')[:8]
    except Exception as e:
        print(f"Error in dashboard view: {e}")
        # Optionally re-raise so you can see the real error
    try:
        from apps.clients.models import Client
        ctx['nouveaux_clients'] = Client.objects.filter(cree_le__month=today.month, cree_le__year=today.year, supprime=False).count()
    except Exception: pass
    try:
        from apps.produits.models import Produit
        ctx['valeur_stock']    = Produit.objects.filter(actif=True, supprime=False).aggregate(v=Sum(F('quantite_stock')*F('prix_achat')))['v'] or 0
        ctx['produits_alerte'] = Produit.objects.filter(quantite_stock__lte=F('seuil_alerte'), actif=True, supprime=False).order_by('quantite_stock')[:5]
    except Exception: pass
    try:
        from apps.services.models import OrdreDeTravail
        ctx['services_actifs'] = OrdreDeTravail.objects.filter(statut__in=['en_attente','en_cours']).count()
        ctx['services_en_cours'] = OrdreDeTravail.objects.filter(statut='en_cours').select_related('client','technicien').order_by('-cree_le')[:5]
    except Exception: pass
    try:
        from apps.locations.models import Location
        ctx['locations_retard'] = Location.objects.filter(statut='en_cours', date_fin_prevue__lt=timezone.now()).count()
    except Exception: pass
    return render(request, 'dashboard/index.html', ctx)
