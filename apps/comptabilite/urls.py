from django.urls import path
from . import views
app_name = 'comptabilite'
urlpatterns = [
    path('',          views.historique,          name='historique'),
    path('nouvelle/', views.ajouter_transaction, name='ajouter'),
]
