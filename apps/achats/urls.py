from django.urls import path
from . import views
app_name = 'achats'
urlpatterns = [
    path('',                     views.liste,       name='liste'),
    path('nouveau/',             views.create,      name='create'),
    path('<int:pk>/',            views.detail,      name='detail'),
    path('<int:pk>/receptionner/',views.receptionner,name='receptionner'),
    path('<int:pk>/payer/',      views.payer,       name='payer'),
    path('<int:pk>/imprimer/',   views.imprimer,    name='imprimer'),
]
