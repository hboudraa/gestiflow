import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import Devis, LigneDevis
from .forms import DevisForm
from apps.core.sanitizers import sanitize_search_query

@login_required
def liste(request):
    q      = sanitize_search_query(request.GET.get('q',''))
    statut = request.GET.get('statut','')
    qs     = Devis.objects.select_related('client','commercial').order_by('-date_devis')
    if q:      qs = qs.filter(Q(numero__icontains=q)|Q(client__nom__icontains=q))
    if statut: qs = qs.filter(statut=statut)
    page = Paginator(qs, 25).get_page(request.GET.get('page'))
    return render(request, 'devis/liste.html', {'devis_list': page, 'q': q, 'statut': statut, 'statuts': Devis.Statut.choices})

@login_required
def detail(request, pk):
    devis = get_object_or_404(Devis, pk=pk)
    return render(request, 'devis/detail.html', {'devis': devis})

@login_required
def create(request):
    initial = {'commercial': request.user, 'date_devis': timezone.now().date(), 'date_validite': timezone.now().date() + timedelta(days=30)}
    form = DevisForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        lignes_data = json.loads(request.POST.get('lignes_json','[]'))
        if not lignes_data:
            messages.error(request, "Ajoutez au moins une ligne.")
        else:
            devis = form.save(commit=False)
            devis.commercial = request.user
            devis.save()
            for i, l in enumerate(lignes_data):
                LigneDevis.objects.create(
                    devis=devis, produit_id=l.get('produit_id') or None,
                    designation=l['designation'], description=l.get('description',''),
                    quantite=Decimal(str(l['quantite'])), prix_unitaire_ht=Decimal(str(l['prix_unitaire_ht'])),
                    remise=Decimal(str(l.get('remise',0))), tva=Decimal(str(l.get('tva',19))), ordre=i,
                )
            devis.calculer_totaux()
            messages.success(request, f"Devis {devis.numero} cree.")
            return redirect('devis:detail', pk=devis.pk)
    return render(request, 'devis/form.html', {'form': form, 'titre': 'Nouveau devis', 'lignes_initiales_json': '[]'})

@login_required
def edit(request, pk):
    devis = get_object_or_404(Devis, pk=pk)
    if devis.statut in ['converti','refuse','expire']:
        messages.error(request, "Ce devis ne peut plus etre modifie.")
        return redirect('devis:detail', pk=pk)
    form = DevisForm(request.POST or None, instance=devis)
    if request.method == 'POST' and form.is_valid():
        form.save()
        lignes_data = json.loads(request.POST.get('lignes_json','[]'))
        if lignes_data:
            devis.lignes.all().delete()
            for i, l in enumerate(lignes_data):
                LigneDevis.objects.create(
                    devis=devis, produit_id=l.get('produit_id') or None,
                    designation=l['designation'], description=l.get('description',''),
                    quantite=Decimal(str(l['quantite'])), prix_unitaire_ht=Decimal(str(l['prix_unitaire_ht'])),
                    remise=Decimal(str(l.get('remise',0))), tva=Decimal(str(l.get('tva',19))), ordre=i,
                )
            devis.calculer_totaux()
        messages.success(request, f"Devis {devis.numero} mis a jour.")
        return redirect('devis:detail', pk=pk)
    lignes = list(devis.lignes.values('produit_id','designation','description','quantite','prix_unitaire_ht','remise','tva'))
    for l in lignes:
        for k in ['quantite','prix_unitaire_ht','remise','tva']:
            if l[k] is not None: l[k] = float(l[k])
    return render(request, 'devis/form.html', {'form': form, 'titre': f'Modifier {devis.numero}', 'devis': devis, 'lignes_initiales_json': json.dumps(lignes)})

@login_required
def convertir(request, pk):
    devis = get_object_or_404(Devis, pk=pk, statut='accepte')
    if request.method == 'POST':
        from apps.ventes.models import Facture, LigneFacture
        facture = Facture.objects.create(client=devis.client, vendeur=request.user, remise_globale=devis.remise_globale, notes=devis.notes)
        for l in devis.lignes.all():
            LigneFacture.objects.create(
                facture=facture, produit=l.produit, designation=l.designation,
                description=l.description, quantite=l.quantite,
                prix_unitaire_ht=l.prix_unitaire_ht, remise=l.remise, tva=l.tva, ordre=l.ordre,
            )
        facture.calculer_totaux()
        devis.statut  = 'converti'
        devis.facture = facture
        devis.save()
        messages.success(request, f"Devis converti en facture {facture.numero}.")
        return redirect('ventes:detail', pk=facture.pk)
    return render(request, 'devis/confirm_convertir.html', {'devis': devis})

@login_required
def changer_statut(request, pk, statut):
    devis = get_object_or_404(Devis, pk=pk)
    statuts_valides = ['brouillon','envoye','accepte','refuse','expire']
    if statut in statuts_valides:
        devis.statut = statut
        devis.save()
        messages.success(request, f"Statut mis a jour : {devis.get_statut_display()}")
    return redirect('devis:detail', pk=pk)

@login_required
def dupliquer(request, pk):
    devis_orig = get_object_or_404(Devis, pk=pk)
    if request.method == 'POST':
        nouveau = Devis.objects.create(
            client=devis_orig.client, commercial=request.user,
            date_devis=timezone.now().date(), date_validite=timezone.now().date()+timedelta(days=30),
            remise_globale=devis_orig.remise_globale, notes=devis_orig.notes, statut='brouillon',
        )
        for l in devis_orig.lignes.all():
            LigneDevis.objects.create(
                devis=nouveau, produit=l.produit, designation=l.designation,
                description=l.description, quantite=l.quantite,
                prix_unitaire_ht=l.prix_unitaire_ht, remise=l.remise, tva=l.tva, ordre=l.ordre,
            )
        nouveau.calculer_totaux()
        messages.success(request, f"Devis duplique → {nouveau.numero}")
        return redirect('devis:detail', pk=nouveau.pk)
    return render(request, 'ventes/confirm_dupliquer.html', {'objet': devis_orig, 'type_doc': 'devis', 'url_action': request.path})

@login_required
def imprimer(request, pk):
    devis = get_object_or_404(Devis, pk=pk)
    from apps.rapports.pdf_generator import generer_pdf_devis
    return generer_pdf_devis(devis)

@login_required
def envoyer_email(request, pk):
    devis = get_object_or_404(Devis, pk=pk)
    if request.method == 'POST':
        destinataire = request.POST.get('destinataire','').strip()
        sujet        = request.POST.get('sujet','').strip()
        corps        = request.POST.get('corps','').strip()
        cc           = request.POST.get('cc','').strip() or None
        from apps.core.email_service import envoyer_devis_email
        ok, msg = envoyer_devis_email(devis, destinataire, sujet, corps, cc)
        if ok:
            if devis.statut == 'brouillon':
                devis.statut = 'envoye'; devis.save()
            messages.success(request, msg)
        else:
            messages.error(request, msg)
        return redirect('devis:detail', pk=pk)
    from django.conf import settings as dj_settings
    nom = dj_settings.GESTIFLOW.get('NOM_ENTREPRISE','Mon Entreprise')
    return JsonResponse({
        'email_client': devis.client.email or '',
        'sujet':  f"Devis {devis.numero} — {nom}",
        'corps':  f"Bonjour,\n\nVeuillez trouver ci-joint notre devis N° {devis.numero} d'un montant de {float(devis.total_ttc):,.2f} DA.\n\nCordialement,\n{nom}",
    })
