from django.urls import path
from . import views
app_name = 'devis'
urlpatterns = [
    path('',                              views.liste,         name='liste'),
    path('nouveau/',                      views.create,        name='create'),
    path('<int:pk>/',                     views.detail,        name='detail'),
    path('<int:pk>/modifier/',            views.edit,          name='edit'),
    path('<int:pk>/convertir/',           views.convertir,     name='convertir'),
    path('<int:pk>/statut/<str:statut>/', views.changer_statut,name='changer_statut'),
    path('<int:pk>/dupliquer/',           views.dupliquer,     name='dupliquer'),
    path('<int:pk>/imprimer/',            views.imprimer,      name='imprimer'),
    path('<int:pk>/envoyer/',             views.envoyer_email, name='envoyer_email'),
]
