from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimestampedModel
from decimal import Decimal

class AchatFournisseur(TimestampedModel):
    class Statut(models.TextChoices):
        EN_ATTENTE  = 'en_attente',  'En attente'
        RECEPTIONNE = 'receptionne', 'Receptionne'
        PAYE        = 'paye',        'Paye'
        ANNULE      = 'annule',      'Annule'

    numero        = models.CharField(max_length=20, unique=True, blank=True)
    fournisseur   = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.PROTECT, related_name='achats')
    cree_par      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date_achat    = models.DateField(default=timezone.now)
    date_reception= models.DateField(null=True, blank=True)
    statut        = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    total_ht      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_tva     = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc     = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes         = models.TextField(blank=True)

    class Meta:
        verbose_name = "Achat fournisseur"
        ordering     = ['-date_achat','-cree_le']

    def __str__(self): return f"Achat {self.numero}"

    def save(self, *args, **kwargs):
        if not self.numero:
            from django.utils import timezone as tz
            year = tz.now().year
            last = AchatFournisseur.objects.filter(numero__startswith=f'ACH{year}').order_by('-numero').first()
            seq  = int(last.numero[7:]) + 1 if last else 1
            self.numero = f"ACH{year}{seq:05d}"
        super().save(*args, **kwargs)

    def calculer_totaux(self, save=True):
        lignes = self.lignes.all()
        self.total_ht  = sum(l.total_ht for l in lignes) or Decimal('0')
        self.total_tva = sum(l.montant_tva for l in lignes) or Decimal('0')
        self.total_ttc = self.total_ht + self.total_tva
        if save:
            self.save()


class LigneAchat(TimestampedModel):
    achat            = models.ForeignKey(AchatFournisseur, on_delete=models.CASCADE, related_name='lignes')
    produit          = models.ForeignKey('produits.Produit', on_delete=models.PROTECT)
    designation      = models.CharField(max_length=300, blank=True)
    quantite         = models.DecimalField(max_digits=12, decimal_places=2)
    prix_unitaire_ht = models.DecimalField(max_digits=12, decimal_places=2)
    tva              = models.DecimalField(max_digits=5,  decimal_places=2, default=19)
    total_ht         = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_tva      = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.designation: self.designation = self.produit.nom
        self.total_ht    = self.quantite * self.prix_unitaire_ht
        self.montant_tva = self.total_ht * self.tva / 100
        super().save(*args, **kwargs)
