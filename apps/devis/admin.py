from django.contrib import admin
from .models import Devis, LigneDevis
class LigneInline(admin.TabularInline):
    model = LigneDevis; extra = 0
@admin.register(Devis)
class DevisAdmin(admin.ModelAdmin):
    list_display = ['numero','client','date_devis','total_ttc','statut']
    list_filter  = ['statut']
    inlines      = [LigneInline]
