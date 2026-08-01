from django.contrib import admin
from .models import AchatFournisseur, LigneAchat
class LigneInline(admin.TabularInline):
    model = LigneAchat; extra = 0
@admin.register(AchatFournisseur)
class AchatAdmin(admin.ModelAdmin):
    list_display = ['numero','fournisseur','date_achat','total_ttc','statut']
    inlines      = [LigneInline]
