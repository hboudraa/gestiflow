from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimestampedModel

class CategorieDepense(TimestampedModel):
    nom = models.CharField(max_length=100, unique=True)
    class Meta: ordering = ['nom']
    def __str__(self): return self.nom

class Transaction(TimestampedModel):
    class Type(models.TextChoices):
        RECETTE = 'recette', 'Recette'
        DEPENSE = 'depense', 'Depense'

    class Mode(models.TextChoices):
        ESPECES  = 'especes',  'Especes'
        VIREMENT = 'virement', 'Virement'
        CHEQUE   = 'cheque',   'Cheque'

    type_transaction  = models.CharField(max_length=10, choices=Type.choices)
    montant           = models.DecimalField(max_digits=14, decimal_places=2)
    libelle           = models.CharField(max_length=200)
    date_transaction  = models.DateField(default=timezone.now)
    mode_reglement    = models.CharField(max_length=20, choices=Mode.choices, default=Mode.ESPECES)
    categorie         = models.ForeignKey(CategorieDepense, on_delete=models.SET_NULL, null=True, blank=True)
    reference         = models.CharField(max_length=100, blank=True)
    valide            = models.BooleanField(default=True)
    cree_par          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Transaction"
        ordering     = ['-date_transaction','-cree_le']

    def __str__(self): return f"{self.type_transaction} — {self.libelle} — {self.montant} DA"
