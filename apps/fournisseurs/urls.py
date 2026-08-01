from django.urls import path
from . import views
app_name = 'fournisseurs'
urlpatterns = [
    path('',                    views.liste,       name='liste'),
    path('nouveau/',            views.create,      name='create'),
    path('<int:pk>/',           views.detail,      name='detail'),
    path('<int:pk>/modifier/',  views.edit,        name='edit'),
    path('<int:pk>/supprimer/', views.delete,      name='delete'),
    path('ajax/recherche/',     views.search_ajax, name='search_ajax'),
]
