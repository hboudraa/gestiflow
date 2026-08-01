from functools import wraps
from django.shortcuts import redirect, render
from django.contrib import messages

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('auth:connexion')
            if request.user.is_superuser or request.user.role in roles:
                return view_func(request, *args, **kwargs)
            return render(request, 'errors/403.html', status=403)
        return _wrapped
    return decorator

def admin_required(view_func):
    return role_required('admin')(view_func)

def manager_required(view_func):
    return role_required('admin', 'manager')(view_func)

def financial_required(view_func):
    return role_required('admin', 'manager', 'comptable')(view_func)
