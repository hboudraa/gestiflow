from django.urls import path
from . import views
app_name = 'services'
urlpatterns = [
    path('',                                  views.liste,               name='liste'),
    path('nouveau/',                          views.create,              name='create'),
    path('mon-espace/',                       views.technicien_dashboard,name='technicien_dashboard'),
    path('<int:pk>/',                         views.detail,              name='detail'),
    path('<int:pk>/modifier/',                views.edit,                name='edit'),
    path('<int:pk>/statut/',                  views.changer_statut,      name='statut'),
    path('<int:pk>/pieces/ajouter/',          views.ajouter_piece,       name='ajouter_piece'),
    path('<int:pk>/outils/ajouter/',          views.ajouter_outil,       name='ajouter_outil'),
    path('<int:pk>/outils/<int:outil_pk>/supprimer/', views.supprimer_outil, name='supprimer_outil'),
    path('<int:pk>/generer-facture/',         views.generer_facture,     name='generer_facture'),
]
