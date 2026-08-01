from django.contrib import admin
from .models import Fournisseur
@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display  = ['code','nom','telephone','email','actif']
    search_fields = ['nom','code']
