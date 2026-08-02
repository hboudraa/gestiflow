from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimestampedModel
from decimal import Decimal

class Devis(TimestampedModel):
    class Statut(models.TextChoices):
        BROUILLON = 'brouillon', 'Brouillon'
        ENVOYE    = 'envoye',    'Envoye'
        ACCEPTE   = 'accepte',   'Accepte'
        REFUSE    = 'refuse',    'Refuse'
        EXPIRE    = 'expire',    'Expire'
        CONVERTI  = 'converti',  'Converti'

    numero         = models.CharField(max_length=20, unique=True, blank=True)
    client         = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='devis')
    commercial     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date_devis     = models.DateField(default=timezone.now)
    date_validite  = models.DateField(null=True, blank=True)
    statut         = models.CharField(max_length=20, choices=Statut.choices, default=Statut.BROUILLON)
    remise_globale = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_ht       = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_tva      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes          = models.TextField(blank=True)
    conditions     = models.TextField(blank=True)
    facture        = models.OneToOneField('ventes.Facture', on_delete=models.SET_NULL, null=True, blank=True, related_name='devis_origine')

    class Meta:
        verbose_name = "Devis"
        ordering     = ['-date_devis','-cree_le']

    def __str__(self): return f"Devis {self.numero}"

    def save(self, *args, **kwargs):
        if not self.numero:
            from django.utils import timezone as tz
            year = tz.now().year
            last = Devis.objects.filter(numero__startswith=f'DEV{year}').order_by('-numero').first()
            seq  = int(last.numero[7:]) + 1 if last else 1
            self.numero = f"DEV{year}{seq:05d}"
        super().save(*args, **kwargs)

    def calculer_totaux(self, save=True):
        lignes    = self.lignes.all()
        total_ht  = sum(l.total_ht for l in lignes) or Decimal('0')
        total_tva = sum(l.montant_tva for l in lignes) or Decimal('0')
        remise    = total_ht * self.remise_globale / Decimal('100')
        self.total_ht  = total_ht - remise
        self.total_tva = total_tva
        self.total_ttc = self.total_ht + total_tva
        if save:
            self.save()


class LigneDevis(TimestampedModel):
    devis            = models.ForeignKey(Devis, on_delete=models.CASCADE, related_name='lignes')
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

    class Meta: ordering = ['ordre','cree_le']

    def save(self, *args, **kwargs):
        self.total_ht    = self.quantite * self.prix_unitaire_ht * (1 - self.remise/100)
        self.montant_tva = self.total_ht * self.tva / 100
        super().save(*args, **kwargs)
