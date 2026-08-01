from django.urls import path
from . import views
app_name = 'auth'
urlpatterns = [
    path('connexion/',              views.connexion,           name='connexion'),
    path('deconnexion/',            views.deconnexion,         name='deconnexion'),
    path('profil/',                 views.profil,              name='profil'),
    path('utilisateurs/',           views.utilisateurs,        name='utilisateurs'),
    path('utilisateurs/nouveau/',   views.utilisateur_create,  name='utilisateur_create'),
    path('utilisateurs/<int:pk>/modifier/', views.utilisateur_edit, name='utilisateur_edit'),
    path('logs/',                   views.logs,                name='logs'),
    path('securite/',               views.security_dashboard,  name='security_dashboard'),
]
