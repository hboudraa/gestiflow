from django.contrib import admin
from .models import Facture, LigneFacture, Paiement
class LigneInline(admin.TabularInline):
    model = LigneFacture; extra = 0
class PaiementInline(admin.TabularInline):
    model = Paiement; extra = 0
@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display  = ['numero','client','date_facture','total_ttc','montant_paye','statut']
    list_filter   = ['statut']
    inlines       = [LigneInline, PaiementInline]
