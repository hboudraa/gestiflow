import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from .models import Facture, LigneFacture, Paiement
from .forms import FactureForm, PaiementForm
from apps.core.sanitizers import sanitize_search_query

@login_required
def liste(request):
    q      = sanitize_search_query(request.GET.get('q',''))
    statut = request.GET.get('statut','')
    qs     = Facture.objects.select_related('client','vendeur').order_by('-date_facture','-cree_le')
    if q:      qs = qs.filter(Q(numero__icontains=q)|Q(client__nom__icontains=q))
    if statut: qs = qs.filter(statut=statut)
    page = Paginator(qs, 25).get_page(request.GET.get('page'))
    totaux = qs.aggregate(ca=Sum('total_ttc'), paye=Sum('montant_paye'))
    return render(request, 'ventes/liste.html', {'factures': page, 'q': q, 'statut': statut, 'totaux': totaux, 'statuts': Facture.Statut.choices})

@login_required
def detail(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    return render(request, 'ventes/detail.html', {'facture': facture})

@login_required
def create(request):
    form = FactureForm(request.POST or None, initial={'vendeur': request.user, 'date_facture': __import__('django.utils.timezone', fromlist=['now']).now().date()})
    if request.method == 'POST' and form.is_valid():
        lignes_data = json.loads(request.POST.get('lignes_json','[]'))
        if not lignes_data:
            messages.error(request, "Ajoutez au moins une ligne.")
        else:
            with transaction.atomic():
                facture = form.save(commit=False)
                facture.vendeur = request.user
                facture.save()
                for i, l in enumerate(lignes_data):
                    LigneFacture.objects.create(
                        facture=facture, produit_id=l.get('produit_id') or None,
                        designation=l['designation'], description=l.get('description',''),
                        quantite=Decimal(str(l['quantite'])), prix_unitaire_ht=Decimal(str(l['prix_unitaire_ht'])),
                        remise=Decimal(str(l.get('remise',0))), tva=Decimal(str(l.get('tva',19))), ordre=i,
                    )
                facture.calculer_totaux()
            messages.success(request, f"Facture {facture.numero} crée.")
            return redirect('ventes:detail', pk=facture.pk)
    from apps.clients.models import Client
    from apps.produits.models import Produit
    return render(request, 'ventes/form.html', {'form': form, 'titre': 'Nouvelle facture', 'lignes_initiales_json': '[]'})

@login_required
def confirmer(request, pk):
    facture = get_object_or_404(Facture, pk=pk, statut='brouillon')
    if request.method == 'POST':
        with transaction.atomic():
            for ligne in facture.lignes.select_related('produit').all():
                if ligne.produit:
                    from apps.produits.models import MouvementStock
                    stock_av = ligne.produit.quantite_stock
                    ligne.produit.quantite_stock = max(Decimal('0'), stock_av - ligne.quantite)
                    ligne.produit.save()
                    MouvementStock.objects.create(
                        produit=ligne.produit, type_mouvement='sortie_vente',
                        quantite=ligne.quantite, stock_avant=stock_av,
                        stock_apres=ligne.produit.quantite_stock,
                        raison=f'Facture {facture.numero}', reference_doc=facture.numero,
                        utilisateur=request.user,
                    )
            facture.statut = 'en_attente'
            facture.save()
        messages.success(request, f"Facture {facture.numero} confirmée.")
    return redirect('ventes:detail', pk=pk)

@login_required
def annuler(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    if request.method == 'POST' and facture.statut != 'annulee':
        facture.statut = 'annulee'
        facture.save()
        messages.success(request, f"Facture {facture.numero} annulée.")
    return redirect('ventes:detail', pk=pk)

@login_required
def ajouter_paiement(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.facture        = facture
            p.enregistre_par = request.user
            p.save()
            facture.montant_paye += p.montant
            facture.save()
            facture.mettre_a_jour_statut()
            messages.success(request, f"Paiement de {p.montant} DA enregistre.")
        else:
            messages.error(request, "Erreur dans le formulaire de paiement.")
    return redirect('ventes:detail', pk=pk)

@login_required
def dupliquer(request, pk):
    facture_orig = get_object_or_404(Facture, pk=pk)
    if request.method == 'POST':
        nouvelle = Facture.objects.create(
            client=facture_orig.client, vendeur=request.user,
            remise_globale=facture_orig.remise_globale, notes=facture_orig.notes, statut='brouillon',
        )
        for l in facture_orig.lignes.all():
            LigneFacture.objects.create(
                facture=nouvelle, produit=l.produit, designation=l.designation,
                description=l.description, quantite=l.quantite,
                prix_unitaire_ht=l.prix_unitaire_ht, remise=l.remise, tva=l.tva, ordre=l.ordre,
            )
        nouvelle.calculer_totaux()
        messages.success(request, f"Facture dupliquee → {nouvelle.numero}")
        return redirect('ventes:detail', pk=nouvelle.pk)
    return render(request, 'ventes/confirm_dupliquer.html', {'objet': facture_orig, 'type_doc': 'facture', 'url_action': request.path})

@login_required
def avoir(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    if request.method == 'POST' and facture.statut not in ['avoir','brouillon']:
        a = Facture.objects.create(client=facture.client, vendeur=request.user, notes=f"Avoir sur {facture.numero}", statut='avoir')
        for l in facture.lignes.all():
            LigneFacture.objects.create(
                facture=a, produit=l.produit, designation=f"[AVOIR] {l.designation}",
                quantite=-abs(l.quantite), prix_unitaire_ht=l.prix_unitaire_ht, remise=l.remise, tva=l.tva,
            )
        a.remise_globale = facture.remise_globale; a.save(); a.calculer_totaux()
        messages.success(request, f"Avoir {a.numero} cree.")
        return redirect('ventes:detail', pk=a.pk)
    return render(request, 'ventes/confirm_avoir.html', {'facture': facture})

@login_required
def imprimer(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    from apps.rapports.pdf_generator import generer_pdf_facture
    return generer_pdf_facture(facture)

@login_required
def envoyer_email(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    if request.method == 'POST':
        destinataire = request.POST.get('destinataire','').strip()
        sujet        = request.POST.get('sujet','').strip()
        corps        = request.POST.get('corps','').strip()
        cc           = request.POST.get('cc','').strip() or None
        from apps.core.email_service import envoyer_facture_email
        ok, msg = envoyer_facture_email(facture, destinataire, sujet, corps, cc)
        if ok: messages.success(request, msg)
        else:  messages.error(request, msg)
        return redirect('ventes:detail', pk=pk)
    from django.conf import settings as dj_settings
    nom = dj_settings.GESTIFLOW.get('NOM_ENTREPRISE','Mon Entreprise')
    return JsonResponse({
        'email_client': facture.client.email or '',
        'sujet':  f"Facture {facture.numero} — {nom}",
        'corps':  f"Bonjour,\n\nVeuillez trouver ci-joint votre facture N° {facture.numero} d'un montant de {float(facture.total_ttc):,.2f} DA.\n\nCordialement,\n{nom}",
    })

@login_required
def paiements_liste(request):
    q    = sanitize_search_query(request.GET.get('q',''))
    mode = request.GET.get('mode','')
    qs   = Paiement.objects.select_related('facture','facture__client','enregistre_par').order_by('-date_paiement')
    if q:    qs = qs.filter(Q(facture__numero__icontains=q)|Q(facture__client__nom__icontains=q))
    if mode: qs = qs.filter(mode=mode)
    total   = qs.aggregate(t=Sum('montant'))['t'] or 0
    page    = Paginator(qs, 25).get_page(request.GET.get('page'))
    return render(request, 'ventes/paiements_liste.html', {'paiements': page, 'q': q, 'mode': mode, 'total_encaisse': total, 'modes': Paiement.Mode.choices})

@login_required
def export_csv(request):
    import csv
    from django.utils import timezone
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="factures_{timezone.now().strftime("%Y%m%d")}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Numero','Date','Client','Total HT','TVA','Total TTC','Paye','Restant','Statut'])
    for f in Facture.objects.select_related('client').order_by('-date_facture'):
        writer.writerow([f.numero, f.date_facture.strftime('%d/%m/%Y'), f.client.nom,
                         float(f.total_ht), float(f.total_tva), float(f.total_ttc),
                         float(f.montant_paye), float(f.montant_restant), f.get_statut_display()])
    return response
