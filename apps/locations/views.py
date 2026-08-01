from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
from .models import Location, ArticleLocation
from .forms import LocationForm
from apps.core.sanitizers import sanitize_search_query

@login_required
def liste(request):
    q      = sanitize_search_query(request.GET.get('q',''))
    statut = request.GET.get('statut','')
    qs     = Location.objects.select_related('client','cree_par').order_by('-date_debut')
    if q:      qs = qs.filter(Q(numero__icontains=q)|Q(client__nom__icontains=q))
    if statut: qs = qs.filter(statut=statut)
    page = Paginator(qs, 25).get_page(request.GET.get('page'))
    return render(request, 'locations/liste.html', {'locations': page, 'q': q, 'statut': statut, 'statuts': Location.Statut.choices})

@login_required
def detail(request, pk):
    location = get_object_or_404(Location, pk=pk)
    return render(request, 'locations/detail.html', {'location': location})

@login_required
def create(request):
    form = LocationForm(request.POST or None)
    if form.is_valid():
        loc = form.save(commit=False)
        loc.cree_par = request.user
        loc.save()
        messages.success(request, f"Location {loc.numero} creee.")
        return redirect('locations:detail', pk=loc.pk)
    return render(request, 'locations/form.html', {'form': form, 'titre': 'Nouvelle location'})

@login_required
def edit(request, pk):
    loc  = get_object_or_404(Location, pk=pk, statut='en_cours')
    form = LocationForm(request.POST or None, instance=loc)
    if form.is_valid():
        form.save()
        messages.success(request, "Location mise a jour.")
        return redirect('locations:detail', pk=pk)
    return render(request, 'locations/form.html', {'form': form, 'titre': f'Modifier {loc.numero}', 'location': loc})

@login_required
def retourner(request, pk):
    loc = get_object_or_404(Location, pk=pk, statut='en_cours')
    if request.method == 'POST':
        now = timezone.now()
        loc.date_fin_reelle = now
        loc.statut = 'terminee'
        if now > loc.date_fin_prevue:
            jours = max(1, (now - loc.date_fin_prevue).days)
            for art in loc.articles.all():
                loc.penalite_retard += art.prix_location_jour * art.quantite * jours * Decimal('0.10')
        loc.calculer_totaux()
        messages.success(request, f"Location {loc.numero} terminee.")
    return redirect('locations:detail', pk=pk)

@login_required
def generer_facture(request, pk):
    loc = get_object_or_404(Location, pk=pk, statut='terminee')
    if loc.facture:
        return redirect('ventes:detail', pk=loc.facture.pk)
    if request.method == 'POST':
        from apps.ventes.models import Facture, LigneFacture
        facture = Facture.objects.create(client=loc.client, vendeur=request.user)
        for art in loc.articles.select_related('produit').all():
            LigneFacture.objects.create(
                facture=facture, produit=art.produit,
                designation=f"Location — {art.produit.nom} ({art.nombre_jours} jour(s))",
                quantite=art.quantite, prix_unitaire_ht=art.prix_location_jour * art.nombre_jours,
                remise=Decimal('0'), tva=Decimal('19'),
            )
        if loc.penalite_retard > 0:
            LigneFacture.objects.create(
                facture=facture, designation="Penalite de retard",
                quantite=Decimal('1'), prix_unitaire_ht=loc.penalite_retard,
                remise=Decimal('0'), tva=Decimal('19'),
            )
        facture.calculer_totaux()
        loc.facture = facture; loc.save(update_fields=['facture'])
        messages.success(request, f"Facture {facture.numero} generee.")
        return redirect('ventes:detail', pk=facture.pk)
    return render(request, 'locations/confirm_facture.html', {'location': loc})

@login_required
def imprimer(request, pk):
    loc = get_object_or_404(Location, pk=pk)
    from apps.rapports.pdf_generator import generer_pdf_location
    return generer_pdf_location(loc)
