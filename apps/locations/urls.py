from django.urls import path
from . import views
app_name = 'locations'
urlpatterns = [
    path('',                        views.liste,           name='liste'),
    path('nouvelle/',               views.create,          name='create'),
    path('<int:pk>/',               views.detail,          name='detail'),
    path('<int:pk>/modifier/',      views.edit,            name='edit'),
    path('<int:pk>/retourner/',     views.retourner,       name='retourner'),
    path('<int:pk>/generer-facture/',views.generer_facture,name='generer_facture'),
    path('<int:pk>/imprimer/',      views.imprimer,        name='imprimer'),
]
