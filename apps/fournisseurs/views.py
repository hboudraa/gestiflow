from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import Fournisseur
from .forms import FournisseurForm
from apps.core.sanitizers import sanitize_search_query

@login_required
def liste(request):
    q  = sanitize_search_query(request.GET.get('q',''))
    qs = Fournisseur.objects.filter(supprime=False)
    if q: qs = qs.filter(Q(nom__icontains=q)|Q(code__icontains=q))
    page = Paginator(qs.order_by('nom'), 25).get_page(request.GET.get('page'))
    return render(request, 'fournisseurs/liste.html', {'fournisseurs': page, 'q': q})

@login_required
def detail(request, pk):
    frn = get_object_or_404(Fournisseur, pk=pk)
    return render(request, 'fournisseurs/detail.html', {'fournisseur': frn})

@login_required
def create(request):
    form = FournisseurForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Fournisseur cree.")
        return redirect('fournisseurs:liste')
    return render(request, 'fournisseurs/form.html', {'form': form, 'titre': 'Nouveau fournisseur'})

@login_required
def edit(request, pk):
    frn  = get_object_or_404(Fournisseur, pk=pk)
    form = FournisseurForm(request.POST or None, instance=frn)
    if form.is_valid():
        form.save()
        messages.success(request, "Fournisseur mis a jour.")
        return redirect('fournisseurs:detail', pk=frn.pk)
    return render(request, 'fournisseurs/form.html', {'form': form, 'titre': f'Modifier — {frn.nom}', 'fournisseur': frn})

@login_required
def delete(request, pk):
    frn = get_object_or_404(Fournisseur, pk=pk)
    if request.method == 'POST':
        frn.supprimer()
        messages.success(request, f"Fournisseur {frn.nom} supprime.")
        return redirect('fournisseurs:liste')
    return render(request, 'fournisseurs/confirm_delete.html', {'fournisseur': frn})

@login_required
def search_ajax(request):
    q  = sanitize_search_query(request.GET.get('q',''))
    qs = Fournisseur.objects.filter(Q(nom__icontains=q)|Q(code__icontains=q), supprime=False)[:10]
    return JsonResponse({'results': [{'id': f.pk, 'text': f'[{f.code}] {f.nom}', 'telephone': f.telephone} for f in qs]})
