from django.db import models
from django.conf import settings


class TimestampedModel(models.Model):
    cree_le     = models.DateTimeField(auto_now_add=True)
    modifie_le  = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(supprime=False)

class SoftDeleteModel(models.Model):
    supprime    = models.BooleanField(default=False)
    supprime_le = models.DateTimeField(null=True, blank=True)
    objects     = SoftDeleteManager()
    all_objects = models.Manager()
    def supprimer(self):
        from django.utils import timezone
        self.supprime    = True
        self.supprime_le = timezone.now()
        self.save()
    class Meta:
        abstract = True


class Adresse(models.Model):
    adresse_ligne1 = models.CharField(max_length=200, blank=True)
    ville          = models.CharField(max_length=100, blank=True)
    wilaya         = models.CharField(max_length=100, blank=True)
    code_postal    = models.CharField(max_length=10,  blank=True)
    @property
    def adresse_complete(self):
        parts = [self.adresse_ligne1, self.ville, self.wilaya]
        return ', '.join(p for p in parts if p)
    class Meta:
        abstract = True


class LogActivite(TimestampedModel):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='logs'
    )
    action      = models.CharField(max_length=300)
    module      = models.CharField(max_length=100, blank=True)
    details     = models.TextField(blank=True)
    adresse_ip  = models.GenericIPAddressField(null=True, blank=True)
    class Meta:
        verbose_name        = "Log d'activite"
        verbose_name_plural = "Logs d'activite"
        ordering            = ['-cree_le']
    def __str__(self):
        return f"{self.action} — {self.cree_le.strftime('%d/%m/%Y %H:%M')}"


class Parametre(models.Model):
    cle         = models.CharField(max_length=100, unique=True)
    valeur      = models.TextField(blank=True)
    description = models.CharField(max_length=200, blank=True)
    class Meta:
        verbose_name        = "Parametre"
        verbose_name_plural = "Parametres"
    def __str__(self):
        return f"{self.cle} = {self.valeur[:40]}"
    @classmethod
    def get(cls, cle, defaut=''):
        try:
            return cls.objects.get(cle=cle).valeur
        except cls.DoesNotExist:
            return defaut
    @classmethod
    def set(cls, cle, valeur):
        obj, _ = cls.objects.get_or_create(cle=cle)
        obj.valeur = str(valeur)
        obj.save()
        return obj
