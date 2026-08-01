from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',        admin.site.urls),
    path('',              include('apps.dashboard.urls',       namespace='dashboard')),
    path('auth/',         include('apps.authentication.urls',  namespace='auth')),
    path('clients/',      include('apps.clients.urls',         namespace='clients')),
    path('fournisseurs/', include('apps.fournisseurs.urls',    namespace='fournisseurs')),
    path('produits/',     include('apps.produits.urls',        namespace='produits')),
    path('ventes/',       include('apps.ventes.urls',          namespace='ventes')),
    path('devis/',        include('apps.devis.urls',           namespace='devis')),
    path('achats/',       include('apps.achats.urls',          namespace='achats')),
    path('locations/',    include('apps.locations.urls',       namespace='locations')),
    path('services/',     include('apps.services.urls',        namespace='services')),
    path('comptabilite/', include('apps.comptabilite.urls',    namespace='comptabilite')),
    path('rapports/',     include('apps.rapports.urls',        namespace='rapports')),
    path('',              include('apps.core.urls',            namespace='core')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'apps.core.views.page_404'
handler500 = 'apps.core.views.page_500'
handler403 = 'apps.core.views.page_403'
