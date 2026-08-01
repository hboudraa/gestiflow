from django.db import models
from django.conf import settings
from apps.core.models import TimestampedModel, SoftDeleteModel
from decimal import Decimal

class Categorie(TimestampedModel):
    nom     = models.CharField(max_length=100, unique=True)
    icone   = models.CharField(max_length=50, blank=True, default='bi-tag')
    couleur = models.CharField(max_length=7,  blank=True, default='#3b82f6')
    class Meta:
        verbose_name        = "Categorie"
        verbose_name_plural = "Categories"
        ordering            = ['nom']
    def __str__(self): return self.nom


class Produit(TimestampedModel, SoftDeleteModel):
    class Unite(models.TextChoices):
        PIECE   = 'pce',    'Piece'
        KG      = 'kg',     'Kilogramme'
        LITRE   = 'l',      'Litre'
        METRE   = 'm',      'Metre'
        BOITE   = 'boite',  'Boite'
        CARTON  = 'carton', 'Carton'
        FORFAIT = 'forfait','Forfait'

    reference       = models.CharField(max_length=50, unique=True, blank=True)
    nom             = models.CharField(max_length=200)
    description     = models.TextField(blank=True)
    categorie       = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True, related_name='produits')
    fournisseur     = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.SET_NULL, null=True, blank=True, related_name='produits')
    code_barre      = models.CharField(max_length=50, blank=True)
    image           = models.ImageField(upload_to='produits/', null=True, blank=True)
    prix_achat      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    prix_vente      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    prix_location   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tva             = models.DecimalField(max_digits=5,  decimal_places=2, default=19)
    unite           = models.CharField(max_length=10, choices=Unite.choices, default=Unite.PIECE)
    quantite_stock  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    seuil_alerte    = models.DecimalField(max_digits=12, decimal_places=2, default=5)
    actif           = models.BooleanField(default=True)
    peut_vendre     = models.BooleanField(default=True)
    peut_louer      = models.BooleanField(default=False)

    class Meta:
        verbose_name        = "Produit"
        verbose_name_plural = "Produits"
        ordering            = ['nom']

    def __str__(self): return f"[{self.reference}] {self.nom}"

    def save(self, *args, **kwargs):
        if not self.reference:
            last = Produit.all_objects.order_by('-id').first()
            self.reference = f"PRD{(last.id + 1 if last else 1):05d}"
        super().save(*args, **kwargs)

    @property
    def en_alerte(self):
        return self.quantite_stock <= self.seuil_alerte

    @property
    def prix_vente_ttc(self):
        return self.prix_vente * (1 + self.tva / Decimal('100'))

    @property
    def marge_brute(self):
        if self.prix_vente > 0:
            return (self.prix_vente - self.prix_achat) / self.prix_vente * 100
        return Decimal('0')


class MouvementStock(TimestampedModel):
    class TypeMouvement(models.TextChoices):
        ENTREE      = 'entree',      'Entree'
        SORTIE_VENTE= 'sortie_vente','Sortie vente'
        SORTIE_SERVICE='sortie_service','Sortie service'
        SORTIE_LOCATION='sortie_location','Sortie location'
        RETOUR_LOCATION='retour_location','Retour location'
        AJUSTEMENT  = 'ajustement', 'Ajustement'
        PERTE       = 'perte',      'Perte/Casse'

    produit        = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement = models.CharField(max_length=20, choices=TypeMouvement.choices)
    quantite       = models.DecimalField(max_digits=12, decimal_places=2)
    stock_avant    = models.DecimalField(max_digits=12, decimal_places=2)
    stock_apres    = models.DecimalField(max_digits=12, decimal_places=2)
    raison         = models.CharField(max_length=200, blank=True)
    reference_doc  = models.CharField(max_length=50,  blank=True)
    utilisateur    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Mouvement de stock"
        ordering     = ['-cree_le']

    def __str__(self):
        return f"{self.produit.nom} — {self.type_mouvement} {self.quantite}"


class HistoriquePrix(models.Model):
    produit            = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='historique_prix')
    ancien_prix_achat  = models.DecimalField(max_digits=12, decimal_places=2)
    nouveau_prix_achat = models.DecimalField(max_digits=12, decimal_places=2)
    ancien_prix_vente  = models.DecimalField(max_digits=12, decimal_places=2)
    nouveau_prix_vente = models.DecimalField(max_digits=12, decimal_places=2)
    modifie_par        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    cree_le            = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-cree_le']
