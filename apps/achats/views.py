import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from .models import AchatFournisseur, LigneAchat
from .forms import AchatForm
from apps.core.sanitizers import sanitize_search_query

@login_required
def liste(request):
    q      = sanitize_search_query(request.GET.get('q',''))
    statut = request.GET.get('statut','')
    qs     = AchatFournisseur.objects.select_related('fournisseur','cree_par').order_by('-date_achat')
    if q:      qs = qs.filter(Q(numero__icontains=q)|Q(fournisseur__nom__icontains=q))
    if statut: qs = qs.filter(statut=statut)
    page = Paginator(qs, 25).get_page(request.GET.get('page'))
    return render(request, 'achats/liste.html', {'achats': page, 'q': q, 'statut': statut, 'statuts': AchatFournisseur.Statut.choices})

@login_required
def detail(request, pk):
    achat = get_object_or_404(AchatFournisseur, pk=pk)
    return render(request, 'achats/detail.html', {'achat': achat})

@login_required
def create(request):
    form = AchatForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        lignes_data = json.loads(request.POST.get('lignes_json','[]'))
        if not lignes_data:
            messages.error(request, "Ajoutez au moins une ligne.")
        else:
            with transaction.atomic():
                achat = form.save(commit=False)
                achat.cree_par = request.user
                achat.save()
                for l in lignes_data:
                    if not l.get('produit_id'): continue
                    LigneAchat.objects.create(
                        achat=achat, produit_id=l['produit_id'],
                        quantite=Decimal(str(l['quantite'])),
                        prix_unitaire_ht=Decimal(str(l['prix_unitaire_ht'])),
                        tva=Decimal(str(l.get('tva',19))),
                    )
                achat.calculer_totaux()
            messages.success(request, f"Achat {achat.numero} cree.")
            return redirect('achats:detail', pk=achat.pk)
    return render(request, 'achats/form.html', {'form': form, 'titre': 'Nouvel achat', 'lignes_initiales_json': '[]'})

@login_required
def receptionner(request, pk):
    achat = get_object_or_404(AchatFournisseur, pk=pk, statut='en_attente')
    if request.method == 'POST':
        with transaction.atomic():
            for ligne in achat.lignes.select_related('produit').all():
                from apps.produits.models import MouvementStock
                stock_av = ligne.produit.quantite_stock
                ligne.produit.quantite_stock += ligne.quantite
                ligne.produit.prix_achat      = ligne.prix_unitaire_ht
                ligne.produit.save()
                MouvementStock.objects.create(
                    produit=ligne.produit, type_mouvement='entree',
                    quantite=ligne.quantite, stock_avant=stock_av,
                    stock_apres=ligne.produit.quantite_stock,
                    raison=f'Achat {achat.numero}', reference_doc=achat.numero,
                    utilisateur=request.user,
                )
            from django.utils import timezone
            achat.statut        = 'receptionne'
            achat.date_reception= timezone.now().date()
            achat.save()
        messages.success(request, f"Achat {achat.numero} receptionne. Stock mis a jour.")
    return redirect('achats:detail', pk=pk)

@login_required
def payer(request, pk):
    achat = get_object_or_404(AchatFournisseur, pk=pk, statut='receptionne')
    if request.method == 'POST':
        achat.statut = 'paye'; achat.save()
        messages.success(request, f"Achat {achat.numero} marque comme paye.")
    return redirect('achats:detail', pk=pk)

@login_required
def imprimer(request, pk):
    achat = get_object_or_404(AchatFournisseur, pk=pk)
    from apps.rapports.pdf_generator import generer_pdf_achat
    return generer_pdf_achat(achat)
