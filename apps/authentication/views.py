from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import ConnexionForm, UtilisateurForm
from .models import Utilisateur, LoginAttempt
from apps.core.decorators import admin_required
from apps.core.security_logger import log_login_success, log_login_failed, log_logout

def connexion(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    bloque, temps = LoginAttempt.est_bloque(request)
    if bloque:
        return render(request, 'authentication/connexion.html', {'form': ConnexionForm(), 'bloque': True, 'temps_restant': temps})
    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user and user.actif:
                login(request, user)
                request.session.cycle_key()
                LoginAttempt.reinitialiser(request)
                log_login_success(request, user)
                user.derniere_activite = timezone.now()
                user.save(update_fields=['derniere_activite'])
                messages.success(request, f"Bienvenue, {user.get_full_name() or user.username} !")
                return redirect(request.GET.get('next', 'dashboard:index'))
            else:
                nb = LoginAttempt.enregistrer_echec(request, form.cleaned_data['username'])
                log_login_failed(request, form.cleaned_data['username'])
                if nb >= 5:
                    bloque, temps = LoginAttempt.est_bloque(request)
                    return render(request, 'authentication/connexion.html', {'form': form, 'bloque': True, 'temps_restant': temps})
                restantes = max(0, 5 - nb)
                messages.error(request, f"Identifiants incorrects. {restantes} tentative(s) restante(s).")
    else:
        form = ConnexionForm()
    return render(request, 'authentication/connexion.html', {'form': form})

def deconnexion(request):
    log_logout(request)
    logout(request)
    return redirect('auth:connexion')

@login_required
def profil(request):
    return render(request, 'authentication/profil.html', {'utilisateur': request.user})

@login_required
@admin_required
def utilisateurs(request):
    qs = Utilisateur.objects.order_by('role', 'first_name')
    return render(request, 'authentication/utilisateurs.html', {'utilisateurs': qs})

@login_required
@admin_required
def utilisateur_create(request):
    form = UtilisateurForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Utilisateur cree avec succes.")
        return redirect('auth:utilisateurs')
    return render(request, 'authentication/utilisateur_form.html', {'form': form, 'titre': 'Nouvel utilisateur'})

@login_required
@admin_required
def utilisateur_edit(request, pk):
    user = get_object_or_404(Utilisateur, pk=pk)
    form = UtilisateurForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        messages.success(request, "Utilisateur mis a jour.")
        return redirect('auth:utilisateurs')
    return render(request, 'authentication/utilisateur_form.html', {'form': form, 'titre': f'Modifier {user.username}', 'utilisateur': user})

@login_required
@admin_required
def logs(request):
    from apps.core.models import LogActivite
    from django.core.paginator import Paginator
    qs = LogActivite.objects.select_related('utilisateur').order_by('-cree_le')
    module = request.GET.get('module', '')
    if module: qs = qs.filter(module=module)
    modules = LogActivite.objects.values_list('module', flat=True).distinct().order_by('module')
    page = Paginator(qs, 30).get_page(request.GET.get('page'))
    return render(request, 'authentication/logs.html', {'logs': page, 'modules_disponibles': modules, 'module_filtre': module})

@login_required
@admin_required
def security_dashboard(request):
    from apps.core.models import LogActivite
    from django.utils import timezone
    from datetime import timedelta
    derniers_7j = timezone.now() - timedelta(days=7)
    connexions_ok    = LogActivite.objects.filter(action='LOGIN_OK', cree_le__gte=derniers_7j).count()
    connexions_echec = LogActivite.objects.filter(action='LOGIN_FAIL', cree_le__gte=derniers_7j).count()
    acces_refuses    = LogActivite.objects.filter(action='ACCESS_DENIED', cree_le__gte=derniers_7j).count()
    ips_bloquees     = LoginAttempt.objects.filter(bloque_jusqu__gt=timezone.now()).order_by('-bloque_jusqu')
    evenements       = LogActivite.objects.filter(module='Securite').select_related('utilisateur').order_by('-cree_le')[:50]
    return render(request, 'authentication/security_dashboard.html', {
        'connexions_ok': connexions_ok, 'connexions_echec': connexions_echec,
        'acces_refuses': acces_refuses, 'ips_bloquees': ips_bloquees,
        'evenements_recents': evenements,
    })
