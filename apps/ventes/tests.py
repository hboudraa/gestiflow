import pytest
from decimal import Decimal
from django.utils import timezone
from apps.clients.models import Client
from apps.produits.models import Produit
from apps.ventes.models import Facture, LigneFacture


@pytest.mark.django_db
class TestFactureNumerotation:
    def test_premier_numero_annee(self):
        client = Client.objects.create(nom="Client Test")
        facture = Facture.objects.create(client=client, date_facture=timezone.now().date())
        annee = timezone.now().year
        assert facture.numero.startswith(f"FAC{annee}")
        assert facture.numero.endswith("00001")

    def test_numeros_incrementaux(self):
        client = Client.objects.create(nom="Client Test")
        f1 = Facture.objects.create(client=client, date_facture=timezone.now().date())
        f2 = Facture.objects.create(client=client, date_facture=timezone.now().date())
        seq1 = int(f1.numero[-5:])
        seq2 = int(f2.numero[-5:])
        assert seq2 == seq1 + 1


@pytest.mark.django_db
class TestFactureCalculs:
    def test_calculer_totaux_sans_save(self):
        client = Client.objects.create(nom="Client Test")
        produit = Produit.objects.create(nom="Produit Test", reference="PRD-T1", prix_achat=100, prix_vente=150, tva=19)
        facture = Facture.objects.create(client=client, date_facture=timezone.now().date())
        LigneFacture.objects.create(facture=facture, produit=produit, designation="Produit Test", quantite=2, prix_unitaire_ht=150, tva=19)

        modifie_avant = facture.modifie_le
        facture.calculer_totaux(save=False)
        facture.refresh_from_db()
        # La base ne doit pas avoir été modifiée (save=False)
        assert facture.modifie_le == modifie_avant

    def test_calculer_totaux_avec_save(self):
        client = Client.objects.create(nom="Client Test")
        produit = Produit.objects.create(nom="Produit Test", reference="PRD-T2", prix_achat=100, prix_vente=150, tva=19)
        facture = Facture.objects.create(client=client, date_facture=timezone.now().date())
        LigneFacture.objects.create(facture=facture, produit=produit, designation="Produit Test", quantite=2, prix_unitaire_ht=150, tva=19)

        facture.calculer_totaux()
        facture.refresh_from_db()
        assert facture.total_ht == Decimal('300.00')
