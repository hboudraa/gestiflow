from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimestampedModel
from decimal import Decimal

class Location(TimestampedModel):
    class Statut(models.TextChoices):
        EN_COURS = 'en_cours', 'En cours'
        TERMINEE = 'terminee', 'Terminee'
        EN_RETARD= 'en_retard','En retard'
        ANNULEE  = 'annulee',  'Annulee'

    numero          = models.CharField(max_length=20, unique=True, blank=True)
    client          = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='locations')
    cree_par        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date_debut      = models.DateTimeField(default=timezone.now)
    date_fin_prevue = models.DateTimeField()
    date_fin_reelle = models.DateTimeField(null=True, blank=True)
    statut          = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_COURS)
    depot_garantie  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalite_retard = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ht        = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_ttc       = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes           = models.TextField(blank=True)
    facture         = models.OneToOneField('ventes.Facture', on_delete=models.SET_NULL, null=True, blank=True, related_name='location')

    class Meta:
        verbose_name = "Location"
        ordering     = ['-date_debut']

    def __str__(self): return f"Location {self.numero}"

    def save(self, *args, **kwargs):
        if not self.numero:
            from django.utils import timezone as tz
            year = tz.now().year
            last = Location.objects.filter(numero__startswith=f'LOC{year}').order_by('-numero').first()
            seq  = int(last.numero[7:]) + 1 if last else 1
            self.numero = f"LOC{year}{seq:05d}"
        super().save(*args, **kwargs)

    @property
    def sous_total_ht(self): return self.total_ht

    def calculer_totaux(self):
        self.total_ht  = sum(a.sous_total_ht for a in self.articles.all()) or Decimal('0')
        self.total_ttc = self.total_ht * Decimal('1.19') + self.penalite_retard
        self.save()


class ArticleLocation(TimestampedModel):
    location         = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='articles')
    produit          = models.ForeignKey('produits.Produit', on_delete=models.PROTECT)
    quantite         = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    prix_location_jour= models.DecimalField(max_digits=12, decimal_places=2)
    nombre_jours     = models.PositiveIntegerField(default=1)

    @property
    def sous_total_ht(self):
        return self.quantite * self.prix_location_jour * self.nombre_jours
