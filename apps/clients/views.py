from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Max, F, ExpressionWrapper, DecimalField
from django.http import JsonResponse, HttpResponse
from .models import Client
from .forms import ClientForm
from apps.core.sanitizers import sanitize_search_query
import logging
logger = logging.getLogger(__name__)

@login_required
def liste(request):
    q   = sanitize_search_query(request.GET.get('q', ''))
    qs  = Client.objects.filter(supprime=False)
    if q: qs = qs.filter(Q(nom__icontains=q)|Q(code__icontains=q)|Q(telephone__icontains=q))
    page = Paginator(qs.order_by('nom'), 25).get_page(request.GET.get('page'))
    return render(request, 'clients/liste.html', {'clients': page, 'q': q})

@login_required
def detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    from django.db.models import Sum
    stats  = {}
    try:
        restant_expr = ExpressionWrapper(F('total_ttc') - F('montant_paye') - F('montant_remise'), output_field=DecimalField())
        stats = client.factures.aggregate(total=Sum('total_ttc'), paye=Sum('montant_paye'), restant=Sum(restant_expr), nb=Count('id'))
    except Exception as e:
        logger.exception(f"Erreur dans detail (stats client {pk}): {e}")
    return render(request, 'clients/detail.html', {'client': client, 'stats': stats})

@login_required
def create(request):
    form = ClientForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Client cree avec succes.")
        return redirect('clients:liste')
    return render(request, 'clients/form.html', {'form': form, 'titre': 'Nouveau client'})

@login_required
def edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form   = ClientForm(request.POST or None, instance=client)
    if form.is_valid():
        form.save()
        messages.success(request, "Client mis a jour.")
        return redirect('clients:detail', pk=client.pk)
    return render(request, 'clients/form.html', {'form': form, 'titre': f'Modifier — {client.nom}', 'client': client})

@login_required
def delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.supprimer()
        messages.success(request, f"Client {client.nom} supprime.")
        return redirect('clients:liste')
    return render(request, 'clients/confirm_delete.html', {'client': client})

@login_required
def rapport(request, pk):
    client  = get_object_or_404(Client, pk=pk)
    from django.utils import timezone
    from apps.ventes.models import Facture, Paiement
    from apps.services.models import OrdreDeTravail
    from apps.locations.models import Location
    from apps.devis.models import Devis
    factures = Facture.objects.filter(client=client).order_by('-date_facture')
    restant_expr = ExpressionWrapper(F('total_ttc') - F('montant_paye') - F('montant_remise'), output_field=DecimalField())
    stats    = factures.aggregate(total_ttc=Sum('total_ttc'), total_paye=Sum('montant_paye'), total_restant=Sum(restant_expr), nb=Count('id'))
    services = OrdreDeTravail.objects.filter(client=client).order_by('-date_entree')
    locations= Location.objects.filter(client=client).order_by('-date_debut')
    devis_list = Devis.objects.filter(client=client).order_by('-date_devis')
    paiements  = Paiement.objects.filter(facture__client=client).select_related('facture').order_by('-date_paiement')
    return render(request, 'clients/rapport.html', {
        'client': client, 'factures': factures, 'stats_factures': stats,
        'services': services, 'locations': locations, 'devis_list': devis_list,
        'paiements': paiements, 'total_paiements': paiements.aggregate(t=Sum('montant'))['t'] or 0,
        'aujourd_hui': timezone.now().date(),
    })

@login_required
def inactifs(request):
    from django.utils import timezone
    from datetime import timedelta
    jours  = int(request.GET.get('jours', 60))
    limite = timezone.now().date() - timedelta(days=jours)
    clients = Client.objects.filter(supprime=False, actif=True).annotate(
        derniere_facture=Max('factures__date_facture'), nb_factures=Count('factures')
    ).filter(Q(derniere_facture__lt=limite)|Q(derniere_facture__isnull=True)).order_by('derniere_facture')
    return render(request, 'clients/inactifs.html', {'clients': clients, 'jours': jours, 'total': clients.count()})

@login_required
def search_ajax(request):
    q  = sanitize_search_query(request.GET.get('q', ''))
    qs = Client.objects.filter(Q(nom__icontains=q)|Q(code__icontains=q), supprime=False)[:10]
    data = [{'id': c.pk, 'text': f'[{c.code}] {c.nom}', 'telephone': c.telephone, 'email': c.email, 'remise_defaut': float(c.remise_defaut)} for c in qs]
    return JsonResponse({'results': data})

@login_required
def remise_ajax(request):
    client_id = request.GET.get('client_id')
    try:
        c = Client.objects.get(pk=client_id, supprime=False)
        return JsonResponse({'remise_defaut': float(c.remise_defaut)})
    except Client.DoesNotExist:
        return JsonResponse({'remise_defaut': 0})

@login_required
def export_csv(request):
    import csv
    from django.utils import timezone
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="clients_{timezone.now().strftime("%Y%m%d")}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Code','Nom','Type','Telephone','Email','Ville','Wilaya','NIF','Remise %','Solde (DA)','Date creation'])
    for c in Client.objects.filter(supprime=False).order_by('nom'):
        writer.writerow([c.code, c.nom, c.get_type_client_display(), c.telephone, c.email,
                         c.ville, c.wilaya, c.nif, float(c.remise_defaut), float(c.solde_en_cours),
                         c.cree_le.strftime('%d/%m/%Y')])
    return response
