from django.contrib import admin
from .models import Produit, Categorie, MouvementStock, HistoriquePrix
admin.site.register(Produit)
admin.site.register(Categorie)
admin.site.register(MouvementStock)
admin.site.register(HistoriquePrix)
