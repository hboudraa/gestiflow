from django.contrib.auth.models import AbstractUser
from django.db import models

class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        ADMIN       = 'admin',       'Administrateur'
        MANAGER     = 'manager',     'Manager'
        VENDEUR     = 'vendeur',     'Vendeur'
        TECHNICIEN  = 'technicien',  'Technicien'
        COMPTABLE   = 'comptable',   'Comptable'
        CAISSIER    = 'caissier',    'Caissier'

    role            = models.CharField(max_length=20, choices=Role.choices, default=Role.VENDEUR)
    telephone       = models.CharField(max_length=20, blank=True)
    actif           = models.BooleanField(default=True)
    derniere_activite = models.DateTimeField(null=True, blank=True)
    photo           = models.ImageField(upload_to='utilisateurs/', null=True, blank=True)

    class Meta:
        verbose_name        = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def est_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def est_manager(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER] or self.is_superuser

    @property
    def est_technicien(self):
        return self.role == self.Role.TECHNICIEN

    @property
    def est_comptable(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER, self.Role.COMPTABLE]


class LoginAttempt(models.Model):
    adresse_ip        = models.GenericIPAddressField()
    username          = models.CharField(max_length=150, blank=True)
    nb_tentatives     = models.PositiveIntegerField(default=0)
    bloque_jusqu      = models.DateTimeField(null=True, blank=True)
    derniere_tentative = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tentative de connexion"
        indexes = [models.Index(fields=['adresse_ip'])]

    @classmethod
    def get_ip(cls, request):
<<<<<<< HEAD
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '0.0.0.0')
=======
        from django.conf import settings
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        # Only trust X-Forwarded-For if explicitly enabled in settings (behind a trusted proxy)
        if getattr(settings, 'USE_X_FORWARDED_FOR', False) and xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
>>>>>>> 1e7c075 (Security: prevent open-redirect, escape email body, validate Excel uploads, X-Forwarded-For opt-in, add CSP whitelist)

    @classmethod
    def est_bloque(cls, request):
        from django.utils import timezone
        ip = cls.get_ip(request)
        try:
            r = cls.objects.get(adresse_ip=ip)
            if r.bloque_jusqu and r.bloque_jusqu > timezone.now():
                secs = int((r.bloque_jusqu - timezone.now()).total_seconds())
                return True, f"{secs//60}m {secs%60}s"
            return False, None
        except cls.DoesNotExist:
            return False, None

    @classmethod
    def enregistrer_echec(cls, request, username=''):
        from django.utils import timezone
        from datetime import timedelta
        ip = cls.get_ip(request)
        r, _ = cls.objects.get_or_create(adresse_ip=ip)
        if r.bloque_jusqu and r.bloque_jusqu <= timezone.now():
            r.nb_tentatives = 0; r.bloque_jusqu = None
        r.username = username[:150]
        r.nb_tentatives += 1
        if r.nb_tentatives >= 5:
            r.bloque_jusqu = timezone.now() + timedelta(minutes=15)
        r.save()
        return r.nb_tentatives

    @classmethod
    def reinitialiser(cls, request):
        cls.objects.filter(adresse_ip=cls.get_ip(request)).delete()
