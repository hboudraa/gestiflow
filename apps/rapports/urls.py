from django.urls import path
from . import views
app_name = 'rapports'
urlpatterns = [
    path('',                    views.index,              name='index'),
    path('ventes/',             views.rapport_ventes,     name='ventes'),
    path('stock/',              views.rapport_stock,      name='stock'),
    path('pl/',                 views.pl_rapport,         name='pl'),
    path('tva/',                views.tva_rapport,        name='tva'),
    path('marges/',             views.marges_rapport,     name='marges'),
    path('vendeurs/',           views.rapport_vendeurs,   name='vendeurs'),
    path('techniciens/',        views.rapport_techniciens,name='techniciens'),
    path('bilan-journalier/',   views.bilan_journalier,   name='bilan_journalier'),
]
