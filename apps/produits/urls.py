from django.urls import path
from . import views
app_name = 'produits'
urlpatterns = [
    path('',                        views.liste,           name='liste'),
    path('nouveau/',                views.create,          name='create'),
    path('<int:pk>/',               views.detail,          name='detail'),
    path('<int:pk>/modifier/',      views.edit,            name='edit'),
    path('<int:pk>/supprimer/',     views.delete,          name='delete'),
    path('<int:pk>/ajuster-stock/', views.ajuster_stock,   name='ajuster_stock'),
    path('alertes/',                views.alertes,         name='alertes'),
    path('categories/',             views.categories,      name='categories'),
    path('categories/nouvelle/',    views.categorie_create,name='categorie_create'),
    path('categories/<int:pk>/modifier/', views.categorie_edit, name='categorie_edit'),
    path('tarif/',                  views.tarif_preview,   name='tarif_preview'),
    path('tarif/pdf/',              views.tarif_pdf,       name='tarif_pdf'),
    path('export/stock/',           views.export_stock_excel, name='export_stock_excel'),
    path('import/',                 views.import_excel,    name='import_excel'),
    path('import/preview/',         views.import_preview,  name='import_preview'),
    path('ajax/recherche/',         views.search_ajax,     name='search_ajax'),
]
