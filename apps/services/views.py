from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
from .models import OrdreDeTravail, PieceService, OutilService, FichierService
from .forms import OrdreDeTravailForm
from apps.core.sanitizers import sanitize_search_query

@login_required
def liste(request):
    q      = sanitize_search_query(request.GET.get('q',''))
    statut = request.GET.get('statut','')
    qs     = OrdreDeTravail.objects.select_related('client','technicien').order_by('-date_entree')
    if request.user.role == 'technicien' and not request.user.est_admin:
        qs = qs.filter(technicien=request.user)
    if q:      qs = qs.filter(Q(numero__icontains=q)|Q(client__nom__icontains=q)|Q(objet_service__icontains=q))
    if statut: qs = qs.filter(statut=statut)
    page = Paginator(qs, 25).get_page(request.GET.get('page'))
    return render(request, 'services/liste.html', {'services': page, 'q': q, 'statut': statut, 'statuts': OrdreDeTravail.Statut.choices})

@login_required
def detail(request, pk):
    service = get_object_or_404(OrdreDeTravail, pk=pk)
    outils = service.outils_utilises.all()
    from apps.produits.models import Produit
    produits_disponibles = Produit.objects.filter(actif=True, supprime=False).order_by('nom')
    return render(request, 'services/detail.html', {
        'service': service,
        'outils_facturables': outils.filter(inclure_dans_facture=True),
        'produits_disponibles': produits_disponibles,
    })

@login_required
def create(request):
    form = OrdreDeTravailForm(request.POST or None)
    if form.is_valid():
        svc = form.save()
        messages.success(request, f"Ordre de travail OT-{svc.numero} cree.")
        return redirect('services:detail', pk=svc.pk)
    return render(request, 'services/form.html', {'form': form, 'titre': 'Nouvel ordre de travail'})

@login_required
def edit(request, pk):
    service = get_object_or_404(OrdreDeTravail, pk=pk)
    form    = OrdreDeTravailForm(request.POST or None, instance=service)
    if form.is_valid():
        form.save()
        messages.success(request, "Service mis a jour.")
        return redirect('services:detail', pk=pk)
    return render(request, 'services/form.html', {'form': form, 'titre': f'Modifier OT-{service.numero}', 'service': service})

@login_required
def changer_statut(request, pk):
    service = get_object_or_404(OrdreDeTravail, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action','')
        today  = timezone.now().date()
        if action == 'demarrer' and service.statut == 'en_attente':
            service.statut = 'en_cours'; service.date_debut_travaux = today
        elif action == 'terminer' and service.statut == 'en_cours':
            service.statut = 'termine'; service.date_fin_reelle = today
        elif action == 'livrer' and service.statut == 'termine':
            service.statut = 'livre'
        elif action == 'suspendre':
            service.statut = 'suspendu'
        elif action == 'annuler':
            service.statut = 'annule'
        service.calculer_totaux()
        messages.success(request, f"Statut : {service.get_statut_display()}")
    return redirect('services:detail', pk=pk)

@login_required
def ajouter_piece(request, pk):
    service = get_object_or_404(OrdreDeTravail, pk=pk)
    if request.method == 'POST':
        produit_id = request.POST.get('produit_id')
        quantite   = Decimal(str(request.POST.get('quantite',1)))
        try:
            from apps.produits.models import Produit, MouvementStock
            produit    = Produit.objects.get(pk=produit_id)
            stock_av   = produit.quantite_stock
            PieceService.objects.create(service=service, produit=produit, quantite=quantite, prix_unitaire_ht=produit.prix_achat)
            produit.quantite_stock = max(Decimal('0'), stock_av - quantite)
            produit.save()
            MouvementStock.objects.create(
                produit=produit, type_mouvement='sortie_service', quantite=quantite,
                stock_avant=stock_av, stock_apres=produit.quantite_stock,
                raison=f'Service OT-{service.numero}', utilisateur=request.user,
            )
            service.calculer_totaux()
            messages.success(request, f"Piece {produit.nom} ajoutee.")
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
    return redirect('services:detail', pk=pk)

@login_required
def ajouter_outil(request, pk):
    service = get_object_or_404(OrdreDeTravail, pk=pk)
    if request.method == 'POST':
        try:
            OutilService.objects.create(
                service=service,
                designation=request.POST.get('designation','').strip(),
                description=request.POST.get('description','').strip(),
                quantite=Decimal(str(request.POST.get('quantite',1))),
                unite=request.POST.get('unite','unite').strip(),
                prix_unitaire_ht=Decimal(str(request.POST.get('prix_unitaire_ht',0))),
                tva=Decimal(str(request.POST.get('tva',19))),
                inclure_dans_facture=request.POST.get('inclure_dans_facture')=='1',
            )
            service.calculer_totaux()
            messages.success(request, "Outil ajoute.")
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
    return redirect('services:detail', pk=pk)

@login_required
def supprimer_outil(request, pk, outil_pk):
    service = get_object_or_404(OrdreDeTravail, pk=pk)
    outil   = get_object_or_404(OutilService, pk=outil_pk, service=service)
    if request.method == 'POST':
        outil.delete(); service.calculer_totaux()
        messages.success(request, "Outil supprime.")
    return redirect('services:detail', pk=pk)

@login_required
def generer_facture(request, pk):
    service = get_object_or_404(OrdreDeTravail, pk=pk)
    if service.statut not in ['termine','livre']:
        messages.error(request, "Service non termine.")
        return redirect('services:detail', pk=pk)
    if service.facture:
        return redirect('ventes:detail', pk=service.facture.pk)
    if request.method == 'POST':
        from apps.ventes.models import Facture, LigneFacture
        facture = Facture.objects.create(client=service.client, vendeur=request.user)
        if service.cout_main_oeuvre > 0:
            LigneFacture.objects.create(
                facture=facture, designation=f"Main d'oeuvre — {service.objet_service}",
                quantite=Decimal('1'), prix_unitaire_ht=service.cout_main_oeuvre, tva=service.tva,
            )
        for p in service.pieces_utilisees.select_related('produit').all():
            LigneFacture.objects.create(
                facture=facture, produit=p.produit, designation=p.produit.nom,
                quantite=p.quantite, prix_unitaire_ht=p.prix_unitaire_ht, tva=Decimal('19'),
            )
        for o in service.outils_utilises.filter(inclure_dans_facture=True).all():
            LigneFacture.objects.create(
                facture=facture, designation=o.designation, description=o.description,
                quantite=o.quantite, prix_unitaire_ht=o.prix_unitaire_ht, tva=o.tva,
            )
        facture.calculer_totaux()
        service.facture = facture; service.save(update_fields=['facture'])
        messages.success(request, f"Facture {facture.numero} generee.")
        return redirect('ventes:detail', pk=facture.pk)
    outils_facturables = service.outils_utilises.filter(inclure_dans_facture=True)
    return render(request, 'services/confirm_facture.html', {'service': service, 'outils_facturables': outils_facturables})

@login_required
def technicien_dashboard(request):
    from django.db.models import Count, Q
    user = request.user
    mes  = OrdreDeTravail.objects.filter(technicien=user).select_related('client').order_by('-cree_le')
    stats = mes.aggregate(
        total=Count('id'),
        nb_attente=Count('id', filter=Q(statut='en_attente')),
        nb_cours=Count('id', filter=Q(statut='en_cours')),
        nb_termine=Count('id', filter=Q(statut__in=['termine','livre'])),
    )
    return render(request, 'services/technicien_dashboard.html', {
        'en_attente': mes.filter(statut='en_attente'),
        'en_cours':   mes.filter(statut='en_cours'),
        'historique': mes.filter(statut__in=['termine','livre'])[:10],
        'stats': stats,
    })
