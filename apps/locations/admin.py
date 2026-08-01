from django.contrib import admin
from .models import Location, ArticleLocation
class ArticleInline(admin.TabularInline):
    model = ArticleLocation; extra = 0
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['numero','client','date_debut','date_fin_prevue','total_ttc','statut']
    inlines      = [ArticleInline]
