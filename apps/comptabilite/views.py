from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Transaction, CategorieDepense
from .forms import TransactionForm
from apps.core.sanitizers import sanitize_search_query

@login_required
def historique(request):
    q      = sanitize_search_query(request.GET.get('q',''))
    type_t = request.GET.get('type','')
    qs     = Transaction.objects.filter(valide=True).select_related('categorie','cree_par').order_by('-date_transaction')
    if q:      qs = qs.filter(Q(libelle__icontains=q)|Q(reference__icontains=q))
    if type_t: qs = qs.filter(type_transaction=type_t)
    totaux = qs.aggregate(recettes=Sum('montant', filter=Q(type_transaction='recette')), depenses=Sum('montant', filter=Q(type_transaction='depense')))
    page   = Paginator(qs, 30).get_page(request.GET.get('page'))
    return render(request, 'comptabilite/historique.html', {'transactions': page, 'q': q, 'type_filtre': type_t, 'totaux': totaux})

@login_required
def ajouter_transaction(request):
    form = TransactionForm(request.POST or None, initial={'date_transaction': timezone.now().date()})
    if form.is_valid():
        t = form.save(commit=False)
        t.cree_par = request.user; t.save()
        messages.success(request, "Transaction enregistree.")
        return redirect('comptabilite:historique')
    return render(request, 'comptabilite/form.html', {'form': form, 'titre': 'Nouvelle transaction'})
