from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimestampedModel
from decimal import Decimal
import re

class OrdreDeTravail(TimestampedModel):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        EN_COURS   = 'en_cours',   'En cours'
        SUSPENDU   = 'suspendu',   'Suspendu'
        TERMINE    = 'termine',    'Termine'
        LIVRE      = 'livre',      'Livre'
        ANNULE     = 'annule',     'Annule'

    class Priorite(models.TextChoices):
        BASSE    = 'basse',    'Basse'
        NORMALE  = 'normale',  'Normale'
        HAUTE    = 'haute',    'Haute'
        URGENTE  = 'urgente',  'Urgente'

    numero              = models.CharField(max_length=20, unique=True, blank=True)
    client              = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='services')
    technicien          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='services_assignes')
    statut              = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    priorite            = models.CharField(max_length=20, choices=Priorite.choices, default=Priorite.NORMALE)
    objet_service       = models.CharField(max_length=200)
    description_probleme= models.TextField(blank=True)
    diagnostic          = models.TextField(blank=True)
    travaux_effectues   = models.TextField(blank=True)
    note_client         = models.TextField(blank=True)
    date_entree         = models.DateField(default=timezone.now)
    date_debut_travaux  = models.DateField(null=True, blank=True)
    date_fin_prevue     = models.DateField(null=True, blank=True)
    date_fin_reelle     = models.DateField(null=True, blank=True)
    cout_main_oeuvre    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cout_pieces         = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tva                 = models.DecimalField(max_digits=5,  decimal_places=2, default=19)
    total_ht            = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc           = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    facture             = models.OneToOneField('ventes.Facture', on_delete=models.SET_NULL, null=True, blank=True, related_name='service')

    class Meta:
        verbose_name = "Ordre de travail"
        ordering     = ['-date_entree','-cree_le']

    def __str__(self): return f"OT-{self.numero}"

    def save(self, *args, **kwargs):
        if not self.numero:
            from django.utils import timezone as tz
            year = tz.now().year
            last = OrdreDeTravail.objects.filter(numero__startswith=f'OT{year}').order_by('-numero').first()
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
            self.numero = f"OT{year}{seq:05d}"
        super().save(*args, **kwargs)

    def calculer_totaux(self, save=True):
        cout_pieces = sum(p.total_ht for p in self.pieces_utilisees.all()) or Decimal('0')
        cout_outils = sum(o.total_ht for o in self.outils_utilises.filter(inclure_dans_facture=True)) or Decimal('0')
        self.cout_pieces = cout_pieces
        self.total_ht    = self.cout_main_oeuvre + cout_pieces + cout_outils
        self.total_ttc   = self.total_ht * (1 + self.tva / Decimal('100'))
        if save:
            self.save()


class PieceService(TimestampedModel):
    service          = models.ForeignKey(OrdreDeTravail, on_delete=models.CASCADE, related_name='pieces_utilisees')
    produit          = models.ForeignKey('produits.Produit', on_delete=models.PROTECT)
    quantite         = models.DecimalField(max_digits=8, decimal_places=2)
    prix_unitaire_ht = models.DecimalField(max_digits=12, decimal_places=2)
    total_ht         = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total_ht = self.quantite * self.prix_unitaire_ht
        super().save(*args, **kwargs)


class OutilService(TimestampedModel):
    service              = models.ForeignKey(OrdreDeTravail, on_delete=models.CASCADE, related_name='outils_utilises')
    designation          = models.CharField(max_length=200)
    description          = models.CharField(max_length=300, blank=True)
    quantite             = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unite                = models.CharField(max_length=30, default='unite')
    prix_unitaire_ht     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tva                  = models.DecimalField(max_digits=5,  decimal_places=2, default=19)
    total_ht             = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    inclure_dans_facture = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.total_ht = self.quantite * self.prix_unitaire_ht
        super().save(*args, **kwargs)


class FichierService(TimestampedModel):
    service   = models.ForeignKey(OrdreDeTravail, on_delete=models.CASCADE, related_name='fichiers')
    fichier   = models.FileField(upload_to='services/')
    nom       = models.CharField(max_length=200, blank=True)
    class Meta: ordering = ['-cree_le']
