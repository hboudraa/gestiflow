from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg, F

@login_required
def index(request):
    reports = [
        ('rapports:ventes',     'bi-receipt',          '#10b981', 'Rapport ventes',           'CA, encaissements, impayés'),
        ('rapports:stock',      'bi-box-seam',         '#f59e0b', 'Rapport stock',            'Inventaire valorisé'),
        ('rapports:pl',         'bi-graph-up-arrow',   '#10b981', 'Compte de résultat (P&L)', 'Revenus, charges, résultat'),
        ('rapports:tva',        'bi-receipt-cutoff',   '#f59e0b', 'Récapitulatif TVA',        'TVA collectée / déductible'),
        ('rapports:marges',     'bi-bar-chart-steps',  '#8b5cf6', 'Analyse des marges',       'Marge par produit'),
        ('rapports:vendeurs',   'bi-people',           '#3b82f6', 'Performance vendeurs',     'CA par vendeur'),
        ('rapports:techniciens','bi-tools',            '#f59e0b', 'Performance techniciens',  'OT terminés, taux'),
        ('rapports:bilan_journalier','bi-calendar-check','#3b82f6','Bilan journalier',       'Résumé du jour'),
    ]
    return render(request, 'rapports/index.html', {'reports': reports})

@login_required
def rapport_ventes(request):
    today  = timezone.now().date()
    debut  = request.GET.get('debut', str(today.replace(day=1)))
    fin    = request.GET.get('fin',   str(today))
    from apps.ventes.models import Facture
    qs = Facture.objects.filter(date_facture__range=[debut,fin], statut__in=['en_attente','partielle','payee']).select_related('client')
    totaux = qs.aggregate(ca=Sum('total_ttc'), paye=Sum('montant_paye'))
    totaux['restant'] = (totaux['ca'] or 0) - (totaux['paye'] or 0)
    return render(request, 'rapports/ventes.html', {'factures': qs.order_by('-date_facture')[:50], 'debut': debut, 'fin': fin, 'totaux': totaux})

@login_required
def rapport_stock(request):
    from apps.produits.models import Produit
    from django.db.models import F as DBF
    produits = Produit.objects.filter(actif=True, supprime=False).select_related('categorie').order_by('categorie__nom','nom')
    valeur_totale = produits.aggregate(v=Sum(DBF('quantite_stock')*DBF('prix_achat')))['v'] or 0
    return render(request, 'rapports/stock.html', {'produits': produits, 'valeur_totale': valeur_totale})

@login_required
def pl_rapport(request):
    today  = timezone.now().date()
    debut  = request.GET.get('debut', str(today.replace(month=1, day=1)))
    fin    = request.GET.get('fin',   str(today))
    from apps.ventes.models import Facture
    from apps.achats.models import AchatFournisseur
    from apps.comptabilite.models import Transaction
    factures_qs = Facture.objects.filter(date_facture__range=[debut,fin], statut__in=['en_attente','partielle','payee'])
    achats_qs   = AchatFournisseur.objects.filter(date_achat__range=[debut,fin], statut__in=['receptionne','paye'])
    ca_ht       = factures_qs.aggregate(t=Sum('total_ht'))['t'] or 0
    ca_ttc      = factures_qs.aggregate(t=Sum('total_ttc'))['t'] or 0
    cout_achats = achats_qs.aggregate(t=Sum('total_ht'))['t'] or 0
    depenses    = Transaction.objects.filter(date_transaction__range=[debut,fin], type_transaction='depense', valide=True).aggregate(t=Sum('montant'))['t'] or 0
    marge_brute = float(ca_ht) - float(cout_achats)
    resultat    = marge_brute - float(depenses)
    taux_marge  = (marge_brute / float(ca_ht) * 100) if ca_ht else 0
    depenses_cat= Transaction.objects.filter(date_transaction__range=[debut,fin], type_transaction='depense', valide=True).values('categorie__nom').annotate(total=Sum('montant')).order_by('-total')
    return render(request, 'rapports/pl.html', {
        'debut': debut, 'fin': fin, 'ca_ht': ca_ht, 'ca_ttc': ca_ttc,
        'cout_achats_ht': cout_achats, 'depenses_caisse': depenses,
        'marge_brute': marge_brute, 'resultat_net': resultat, 'taux_marge': taux_marge,
        'nb_factures': factures_qs.count(), 'nb_achats': achats_qs.count(),
        'depenses_par_categorie': depenses_cat,
    })

@login_required
def tva_rapport(request):
    today  = timezone.now().date()
    debut  = request.GET.get('debut', str(today.replace(day=1)))
    fin    = request.GET.get('fin',   str(today))
    from apps.ventes.models import LigneFacture
    from apps.achats.models import LigneAchat
    lv = LigneFacture.objects.filter(facture__date_facture__range=[debut,fin], facture__statut__in=['en_attente','partielle','payee'])
    la = LigneAchat.objects.filter(achat__date_achat__range=[debut,fin], achat__statut__in=['receptionne','paye'])
    tva_col  = lv.aggregate(t=Sum('montant_tva'))['t'] or 0
    tva_ded  = la.aggregate(t=Sum('montant_tva'))['t'] or 0
    base_v   = lv.aggregate(t=Sum('total_ht'))['t'] or 0
    base_a   = la.aggregate(t=Sum('total_ht'))['t'] or 0
    tva_ventes_par_taux = lv.values('tva').annotate(base_ht=Sum('total_ht'), montant_tva=Sum('montant_tva')).order_by('tva')
    tva_achats_par_taux = la.values('tva').annotate(base_ht=Sum('total_ht'), montant_tva=Sum('montant_tva')).order_by('tva')
    return render(request, 'rapports/tva.html', {
        'debut': debut, 'fin': fin,
        'tva_collectee': tva_col, 'tva_deductible': tva_ded,
        'base_ht_ventes': base_v, 'base_ht_achats': base_a,
        'solde_tva': float(tva_col) - float(tva_ded),
        'tva_ventes_par_taux': tva_ventes_par_taux,
        'tva_achats_par_taux': tva_achats_par_taux,
    })

@login_required
def marges_rapport(request):
    from apps.produits.models import Produit, Categorie
    from apps.ventes.models import LigneFacture
    cat_id = request.GET.get('categorie','')
    tri    = request.GET.get('tri','marge_desc')
    qs     = Produit.objects.filter(actif=True, supprime=False, peut_vendre=True).select_related('categorie')
    if cat_id: qs = qs.filter(categorie_id=cat_id)
    resultats = []
    for p in qs:
        v = LigneFacture.objects.filter(produit=p, facture__statut__in=['en_attente','partielle','payee']).aggregate(qte=Sum('quantite'), ca=Sum('total_ht'))
        qte = float(v['qte'] or 0); ca = float(v['ca'] or 0)
        cout = qte * float(p.prix_achat)
        marge_da = ca - cout
        marge_pct = (marge_da / ca * 100) if ca > 0 else 0
        resultats.append({'produit': p, 'qte_vendue': qte, 'ca_ht': ca, 'cout_total': cout, 'marge_da': marge_da, 'marge_pct': marge_pct, 'valeur_stock': float(p.quantite_stock)*float(p.prix_achat)})
    if tri == 'marge_desc': resultats.sort(key=lambda x: x['marge_pct'], reverse=True)
    elif tri == 'marge_asc': resultats.sort(key=lambda x: x['marge_pct'])
    elif tri == 'ca_desc':   resultats.sort(key=lambda x: x['ca_ht'], reverse=True)
    total_ca    = sum(r['ca_ht'] for r in resultats)
    total_cout  = sum(r['cout_total'] for r in resultats)
    total_marge = total_ca - total_cout
    taux_moyen  = (total_marge / total_ca * 100) if total_ca > 0 else 0
    return render(request, 'rapports/marges.html', {
        'resultats': resultats, 'categories': Produit._meta.get_field('categorie').related_model.objects.all().order_by('nom'),
        'categorie_id': cat_id, 'tri': tri,
        'total_ca': total_ca, 'total_cout': total_cout, 'total_marge': total_marge, 'taux_moyen': taux_moyen,
    })

@login_required
def rapport_vendeurs(request):
    today = timezone.now().date()
    debut = request.GET.get('debut', str(today.replace(day=1)))
    fin   = request.GET.get('fin',   str(today))
    from apps.ventes.models import Facture
    stats = (Facture.objects.filter(date_facture__range=[debut,fin], statut__in=['en_attente','partielle','payee'], vendeur__isnull=False)
             .values('vendeur__id','vendeur__first_name','vendeur__last_name','vendeur__username')
             .annotate(nb_factures=Count('id'), total_ttc=Sum('total_ttc'), total_paye=Sum('montant_paye'))
             .order_by('-total_ttc'))
    grand_total = sum(s['total_ttc'] or 0 for s in stats)
    for s in stats:
        s['total_restant'] = float(s['total_ttc'] or 0) - float(s['total_paye'] or 0)
        s['pct_ca']      = float(s['total_ttc'] or 0)/float(grand_total)*100 if grand_total else 0
        s['nom_complet'] = f"{s['vendeur__first_name']} {s['vendeur__last_name']}".strip() or s['vendeur__username']
    return render(request, 'rapports/vendeurs.html', {'stats': stats, 'debut': debut, 'fin': fin, 'grand_total': grand_total})

@login_required
def rapport_techniciens(request):
    today = timezone.now().date()
    debut = request.GET.get('debut', str(today.replace(day=1)))
    fin   = request.GET.get('fin',   str(today))
    from apps.services.models import OrdreDeTravail
    stats = (OrdreDeTravail.objects.filter(date_entree__range=[debut,fin], technicien__isnull=False)
             .values('technicien__id','technicien__first_name','technicien__last_name','technicien__username')
             .annotate(total_ot=Count('id'), nb_termine=Count('id', filter=Q(statut__in=['termine','livre'])), nb_en_cours=Count('id', filter=Q(statut='en_cours')), nb_attente=Count('id', filter=Q(statut='en_attente')), ca_services=Sum('total_ttc'))
             .order_by('-nb_termine'))
    for s in stats:
        s['nom_complet']     = f"{s['technicien__first_name']} {s['technicien__last_name']}".strip() or s['technicien__username']
        s['taux_completion'] = s['nb_termine']/s['total_ot']*100 if s['total_ot'] > 0 else 0
    return render(request, 'rapports/techniciens.html', {'stats': stats, 'debut': debut, 'fin': fin})

@login_required
def bilan_journalier(request):
    today = timezone.now().date()
    from apps.ventes.models import Facture, Paiement
    from apps.services.models import OrdreDeTravail
    from apps.produits.models import Produit
    from django.db.models import F as DBF
    factures_jour    = Facture.objects.filter(date_facture=today, statut__in=['en_attente','partielle','payee']).select_related('client').order_by('-cree_le')
    ca_jour          = factures_jour.aggregate(t=Sum('total_ttc'))['t'] or 0
    paiements_jour   = Paiement.objects.filter(date_paiement=today).aggregate(t=Sum('montant'))['t'] or 0
    services_termines= OrdreDeTravail.objects.filter(date_fin_reelle=today, statut__in=['termine','livre']).select_related('client')
    alertes_stock    = Produit.objects.filter(actif=True, supprime=False, quantite_stock__lte=DBF('seuil_alerte')).count()
    if request.GET.get('pdf') == '1':
        from apps.rapports.pdf_generator import generer_pdf_bilan_journalier
        return generer_pdf_bilan_journalier(today, {
            'factures': factures_jour, 'services_termines': services_termines,
            'ca_jour': ca_jour, 'encaisse_jour': paiements_jour,
            'nb_factures': factures_jour.count(), 'alertes_stock': alertes_stock,
        })
    return render(request, 'rapports/bilan_journalier.html', {
        'aujourd_hui': today, 'factures_jour': factures_jour, 'ca_jour': ca_jour,
        'paiements_jour': paiements_jour, 'services_termines': services_termines,
        'alertes_stock': alertes_stock, 'nb_factures': factures_jour.count(),
    })
