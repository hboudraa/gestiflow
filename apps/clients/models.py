from django.db import models
from apps.core.models import TimestampedModel, SoftDeleteModel, Adresse
import logging
logger = logging.getLogger(__name__)

class Client(TimestampedModel, SoftDeleteModel, Adresse):
    class TypeClient(models.TextChoices):
        PARTICULIER    = 'particulier',    'Particulier'
        ENTREPRISE     = 'entreprise',     'Entreprise'
        ADMINISTRATION = 'administration', 'Administration'

    code             = models.CharField(max_length=20, unique=True, blank=True)
    nom              = models.CharField(max_length=200)
    type_client      = models.CharField(max_length=20, choices=TypeClient.choices, default=TypeClient.PARTICULIER)
    telephone        = models.CharField(max_length=20, blank=True)
    telephone2       = models.CharField(max_length=20, blank=True)
    email            = models.EmailField(blank=True)
    registre_commerce = models.CharField(max_length=50, blank=True)
    nif              = models.CharField(max_length=20, blank=True)
    nis              = models.CharField(max_length=20, blank=True)
    limite_credit    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    remise_defaut    = models.DecimalField(max_digits=5,  decimal_places=2, default=0)
    notes            = models.TextField(blank=True)
    actif            = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Client"
        verbose_name_plural = "Clients"
        ordering            = ['nom']

    def __str__(self):
        return f"[{self.code}] {self.nom}"

    def save(self, *args, **kwargs):
        if not self.code:
            last = Client.all_objects.order_by('-id').first()
            self.code = f"CLT{(last.id + 1 if last else 1):05d}"
        super().save(*args, **kwargs)

    @property
    def solde_en_cours(self):
        try:
            from django.db.models import Sum
            r = self.factures.filter(statut__in=['en_attente','partielle']).aggregate(
                ttc=Sum('total_ttc'), paye=Sum('montant_paye'), remise=Sum('montant_remise'))
            return (r['ttc'] or 0) - (r['paye'] or 0) - (r['remise'] or 0)
        except Exception as e:
            logger.exception(f"Erreur dans Client.solde_en_cours ({self.pk}): {e}")
            return 0
