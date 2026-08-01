from django.urls import path
from . import views
app_name = 'clients'
urlpatterns = [
    path('',                    views.liste,        name='liste'),
    path('nouveau/',            views.create,       name='create'),
    path('<int:pk>/',           views.detail,       name='detail'),
    path('<int:pk>/modifier/',  views.edit,         name='edit'),
    path('<int:pk>/supprimer/', views.delete,       name='delete'),
    path('<int:pk>/rapport/',   views.rapport,      name='rapport'),
    path('inactifs/',           views.inactifs,     name='inactifs'),
    path('ajax/recherche/',     views.search_ajax,  name='search_ajax'),
    path('ajax/remise/',        views.remise_ajax,  name='remise_ajax'),
    path('export/csv/',         views.export_csv,   name='export_csv'),
]
