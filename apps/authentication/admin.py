from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, LoginAttempt

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display  = ['username','get_full_name','role','actif','last_login']
    list_filter   = ['role','actif']
    fieldsets     = UserAdmin.fieldsets + (('GestiFlow', {'fields': ('role','telephone','actif')}),)

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['adresse_ip','username','nb_tentatives','bloque_jusqu','derniere_tentative']
