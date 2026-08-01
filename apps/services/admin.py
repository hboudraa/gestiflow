from django.contrib import admin
from .models import OrdreDeTravail, PieceService, OutilService
class PieceInline(admin.TabularInline):
    model = PieceService; extra = 0
class OutilInline(admin.TabularInline):
    model = OutilService; extra = 0
@admin.register(OrdreDeTravail)
class OTAdmin(admin.ModelAdmin):
    list_display = ['numero','client','technicien','priorite','statut','date_entree']
    list_filter  = ['statut','priorite']
    inlines      = [PieceInline, OutilInline]
