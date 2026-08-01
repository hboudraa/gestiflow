from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

def page_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def page_500(request):
    return render(request, 'errors/500.html', status=500)

def page_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)

@login_required
def recherche_globale(request):
    from apps.core.sanitizers import sanitize_search_query
    from django.db.models import Q
    q = sanitize_search_query(request.GET.get('q', ''))
    resultats = {}
    if q and len(q) >= 2:
        try:
            from apps.clients.models import Client
            resultats['clients'] = Client.objects.filter(Q(nom__icontains=q)|Q(code__icontains=q), supprime=False)[:8]
        except Exception: pass
        try:
            from apps.produits.models import Produit
            resultats['produits'] = Produit.objects.filter(Q(nom__icontains=q)|Q(reference__icontains=q), supprime=False)[:8]
        except Exception: pass
        try:
            from apps.ventes.models import Facture
            resultats['factures'] = Facture.objects.filter(Q(numero__icontains=q)|Q(client__nom__icontains=q)).select_related('client')[:6]
        except Exception: pass
        try:
            from apps.devis.models import Devis
            resultats['devis'] = Devis.objects.filter(Q(numero__icontains=q)|Q(client__nom__icontains=q)).select_related('client')[:5]
        except Exception: pass
    total = sum(len(v) for v in resultats.values())
    return render(request, 'core/recherche_globale.html', {'q': q, 'resultats': resultats, 'total': total})

@login_required
def recherche_ajax(request):
    from apps.core.sanitizers import sanitize_search_query
    from django.db.models import Q
    q = sanitize_search_query(request.GET.get('q', ''))
    data = []
    if len(q) >= 2:
        try:
            from apps.clients.models import Client
            for c in Client.objects.filter(Q(nom__icontains=q)|Q(code__icontains=q), supprime=False)[:4]:
                data.append({'type':'Client','icon':'bi-person','label':c.nom,'sub':c.code,'url':f'/clients/{c.pk}/'})
        except Exception: pass
        try:
            from apps.produits.models import Produit
            for p in Produit.objects.filter(Q(nom__icontains=q)|Q(reference__icontains=q), supprime=False)[:4]:
                data.append({'type':'Produit','icon':'bi-box-seam','label':p.nom,'sub':p.reference,'url':f'/produits/{p.pk}/'})
        except Exception: pass
        try:
            from apps.ventes.models import Facture
            for f in Facture.objects.filter(Q(numero__icontains=q)|Q(client__nom__icontains=q)).select_related('client')[:3]:
                data.append({'type':'Facture','icon':'bi-receipt','label':f.numero,'sub':f.client.nom,'url':f'/ventes/{f.pk}/'})
        except Exception: pass
    return JsonResponse({'results': data, 'query': q})

@login_required
def notifications(request):
    from apps.core.notifications import get_all_notifications
    notifs = get_all_notifications(request.user)
    total  = sum(len(v) for v in notifs.values())
    return render(request, 'core/notifications.html', {'notifs': notifs, 'total': total})

@login_required
def parametres(request):
    if not request.user.est_admin:
        messages.error(request, "Acces reserve a l'administrateur.")
        return redirect('dashboard:index')
    from apps.core.models import Parametre
    cles = [
        ('NOM_ENTREPRISE', "Nom de l'entreprise", 'text'),
        ('ADRESSE',        'Adresse',              'text'),
        ('TELEPHONE',      'Telephone',            'text'),
        ('EMAIL',          'Email de contact',     'email'),
        ('DEVISE',         'Devise (DA, EUR...)',   'text'),
        ('TVA_DEFAUT',     'TVA par defaut (%)',    'number'),
    ]
    if request.method == 'POST':
        if request.POST.get('test_email') == '1':
            from apps.core.email_service import tester_configuration_email
            ok, msg = tester_configuration_email() if hasattr(__import__('apps.core.email_service', fromlist=['tester_configuration_email']), 'tester_configuration_email') else (False, 'Non configure')
            if ok: messages.success(request, f'✅ {msg}')
            else:  messages.error(request, f'❌ {msg}')
            return redirect('core:parametres')
        for cle, _, _ in cles:
            val = request.POST.get(cle, '').strip()
            if val: Parametre.set(cle, val)
        if 'logo' in request.FILES:
            import os
            logo_file = request.FILES['logo']
            logo_dir  = os.path.join('media', 'parametres')
            os.makedirs(logo_dir, exist_ok=True)
            with open(os.path.join(logo_dir, 'logo.png'), 'wb') as f:
                for chunk in logo_file.chunks(): f.write(chunk)
            Parametre.set('LOGO', '/media/parametres/logo.png')
        messages.success(request, 'Parametres mis a jour.')
        return redirect('core:parametres')
    valeurs = {cle: Parametre.get(cle, '') for cle, _, _ in cles}
    logo    = Parametre.get('LOGO', '')
    admin_links = [
        ('/auth/utilisateurs/', 'bi-people', 'Gérer les utilisateurs'),
        ('/auth/logs/', 'bi-journal-text', "Journal d'activité"),
        ('/auth/securite/', 'bi-shield-check', 'Sécurité'),
        ('/admin/', 'bi-gear', 'Admin Django'),
    ]
    return render(request, 'parametres/index.html', {
        'cles': cles, 'valeurs': valeurs, 'logo': logo, 'admin_links': admin_links
    })
