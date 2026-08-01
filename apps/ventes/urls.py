from django.urls import path
from . import views
app_name = 'ventes'
urlpatterns = [
    path('',                        views.liste,           name='liste'),
    path('nouvelle/',               views.create,          name='create'),
    path('<int:pk>/',               views.detail,          name='detail'),
    path('<int:pk>/confirmer/',     views.confirmer,       name='confirmer'),
    path('<int:pk>/annuler/',       views.annuler,         name='annuler'),
    path('<int:pk>/paiement/',      views.ajouter_paiement,name='ajouter_paiement'),
    path('<int:pk>/dupliquer/',     views.dupliquer,       name='dupliquer'),
    path('<int:pk>/avoir/',         views.avoir,           name='avoir'),
    path('<int:pk>/imprimer/',      views.imprimer,        name='imprimer'),
    path('<int:pk>/envoyer/',       views.envoyer_email,   name='envoyer_email'),
    path('paiements/',              views.paiements_liste, name='paiements_liste'),
    path('export/csv/',             views.export_csv,      name='export_csv'),
]
