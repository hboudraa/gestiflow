import pytest
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from apps.clients.models import Client
from apps.locations.models import Location, ArticleLocation
from apps.produits.models import Produit


@pytest.mark.django_db
class TestLocationTVA:
    def test_tva_utilise_parametre_settings(self):
        client = Client.objects.create(nom="Client Test")
        location = Location.objects.create(
            client=client,
            date_debut=timezone.now(),
            date_fin_prevue=timezone.now(),
        )
        produit = Produit.objects.create(nom="Produit Location", prix_location=100)
        ArticleLocation.objects.create(
            location=location,
            produit=produit,
            quantite=1,
            prix_location_jour=Decimal('100.00'),
            nombre_jours=1,
        )
        location.calculer_totaux()
        location.refresh_from_db()
        tva_pct = Decimal(str(settings.GESTIFLOW.get('TVA_DEFAUT', '19')))
        attendu = Decimal('100.00') * (Decimal('1') + tva_pct / Decimal('100'))
        assert location.total_ttc == attendu
