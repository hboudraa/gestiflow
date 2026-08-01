from django.urls import path
from . import views
app_name = 'core'
urlpatterns = [
    path('recherche/',       views.recherche_globale, name='recherche'),
    path('recherche/ajax/',  views.recherche_ajax,    name='recherche_ajax'),
    path('notifications/',   views.notifications,     name='notifications'),
    path('parametres/',      views.parametres,        name='parametres'),
]
