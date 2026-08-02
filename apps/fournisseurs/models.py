from django.db import models
from apps.core.models import TimestampedModel, SoftDeleteModel, Adresse
import logging
logger = logging.getLogger(__name__)

class Fournisseur(TimestampedModel, SoftDeleteModel, Adresse):
    code              = models.CharField(max_length=20, unique=True, blank=True)
    nom               = models.CharField(max_length=200)
    telephone         = models.CharField(max_length=20, blank=True)
    telephone2        = models.CharField(max_length=20, blank=True)
    email             = models.EmailField(blank=True)
    contact_nom       = models.CharField(max_length=100, blank=True)
    registre_commerce = models.CharField(max_length=50, blank=True)
    nif               = models.CharField(max_length=20, blank=True)
    delai_paiement    = models.PositiveIntegerField(default=30, help_text='Jours')
    remise_habituelle = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes             = models.TextField(blank=True)
    actif             = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering            = ['nom']

    def __str__(self):
        return f"[{self.code}] {self.nom}"

    def save(self, *args, **kwargs):
        if not self.code:
            last = Fournisseur.all_objects.order_by('-id').first()
            self.code = f"FRN{(last.id + 1 if last else 1):05d}"
        super().save(*args, **kwargs)

    @property
    def solde_du(self):
        try:
            from django.db.models import Sum
            r = self.achats.filter(statut__in=['en_attente','receptionne']).aggregate(t=Sum('total_ttc'))
            return r['t'] or 0
        except Exception as e:
            logger.exception(f"Erreur dans Fournisseur.solde_du ({self.pk}): {e}")
            return 0
