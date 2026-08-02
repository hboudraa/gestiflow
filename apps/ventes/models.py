from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimestampedModel
from decimal import Decimal
import re

class Facture(TimestampedModel):
    class Statut(models.TextChoices):
        BROUILLON  = 'brouillon',  'Brouillon'
        EN_ATTENTE = 'en_attente', 'En attente'
        PARTIELLE  = 'partielle',  'Partiellement payee'
        PAYEE      = 'payee',      'Payee'
        ANNULEE    = 'annulee',    'Annulee'
        AVOIR      = 'avoir',      'Avoir'

    numero         = models.CharField(max_length=20, unique=True, blank=True)
    client         = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='factures')
    vendeur        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='factures_vendues')
    date_facture   = models.DateField(default=timezone.now)
    date_echeance  = models.DateField(null=True, blank=True)
    statut         = models.CharField(max_length=20, choices=Statut.choices, default=Statut.BROUILLON)
    remise_globale = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sous_total_ht  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_remise = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ht       = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_tva      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_paye   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes          = models.TextField(blank=True)
    conditions     = models.TextField(blank=True)

    class Meta:
        verbose_name = "Facture"
        ordering     = ['-date_facture','-cree_le']

    def __str__(self): return f"Facture {self.numero}"

    def save(self, *args, **kwargs):
        if not self.numero:
            from django.utils import timezone as tz
            year = tz.now().year
            last = Facture.objects.filter(numero__startswith=f'FAC{year}').order_by('-numero').first()
            if last:
                match = re.search(r'(\d+)$', last.numero)
                if match:
                    trailing = match.group(1)
                    annee = str(year)
                    seq = int(trailing[len(annee):]) + 1 if trailing.startswith(annee) and trailing != annee else int(trailing) + 1
                else:
                    seq = 1
            else:
                seq = 1
            self.numero = f"FAC{year}{seq:05d}"
        super().save(*args, **kwargs)

    @property
    def montant_restant(self):
        return max(Decimal('0'), self.total_ttc - self.montant_paye)

    def calculer_totaux(self, save=True):
        lignes = self.lignes.all()
        sous_total = sum(l.total_ht for l in lignes) or Decimal('0')
        remise_amt = sous_total * self.remise_globale / Decimal('100')
        total_ht   = sous_total - remise_amt
        total_tva  = sum(l.montant_tva for l in lignes) or Decimal('0')
        self.sous_total_ht  = sous_total
        self.montant_remise = remise_amt
        self.total_ht       = total_ht
        self.total_tva      = total_tva
        self.total_ttc      = total_ht + total_tva
        if save:
            self.save()

    def mettre_a_jour_statut(self):
        if self.statut in ['annulee','avoir','brouillon']: return
        if self.montant_paye <= 0:
            self.statut = 'en_attente'
        elif self.montant_paye >= self.total_ttc:
            self.statut = 'payee'
        else:
            self.statut = 'partielle'
        self.save()


class LigneFacture(TimestampedModel):
    facture          = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    produit          = models.ForeignKey('produits.Produit', on_delete=models.SET_NULL, null=True, blank=True)
    designation      = models.CharField(max_length=300)
    description      = models.TextField(blank=True)
    quantite         = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    prix_unitaire_ht = models.DecimalField(max_digits=12, decimal_places=2)
    remise           = models.DecimalField(max_digits=5,  decimal_places=2, default=0)
    tva              = models.DecimalField(max_digits=5,  decimal_places=2, default=19)
    total_ht         = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_tva      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    ordre            = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre','cree_le']

    def save(self, *args, **kwargs):
        self.total_ht    = self.quantite * self.prix_unitaire_ht * (1 - self.remise/100)
        self.montant_tva = self.total_ht * self.tva / 100
        super().save(*args, **kwargs)


class Paiement(TimestampedModel):
    class Mode(models.TextChoices):
        ESPECES  = 'especes',  'Especes'
        VIREMENT = 'virement', 'Virement'
        CHEQUE   = 'cheque',   'Cheque'
        CB       = 'cb',       'Carte bancaire'
        CREDIT   = 'credit',   'Credit'

    facture       = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='paiements')
    montant       = models.DecimalField(max_digits=14, decimal_places=2)
    date_paiement = models.DateField(default=timezone.now)
    mode          = models.CharField(max_length=20, choices=Mode.choices, default=Mode.ESPECES)
    reference     = models.CharField(max_length=100, blank=True)
    notes         = models.TextField(blank=True)
    enregistre_par= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Paiement"
        ordering     = ['-date_paiement']

    def __str__(self): return f"Paiement {self.montant} DA — {self.facture.numero}"
