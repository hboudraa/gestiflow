import environ, os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG       = env.bool('DEBUG', default=False)
# ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', '192.168.0.196'])
ALLOWED_HOSTS = list(set(env.list('ALLOWED_HOSTS', default=[]) + ['127.0.0.1', 'localhost', '192.168.0.165', '192.168.0.196']))
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'crispy_forms',
    'crispy_bootstrap5',
    'import_export',
    # GestiFlow apps
    'apps.core',
    'apps.authentication',
    'apps.dashboard',
    'apps.clients',
    'apps.fournisseurs',
    'apps.produits',
    'apps.ventes',
    'apps.devis',
    'apps.achats',
    'apps.locations',
    'apps.services',
    'apps.comptabilite',
    'apps.rapports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'apps.core.security_middleware.SecurityHeadersMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF     = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
AUTH_USER_MODEL  = 'authentication.Utilisateur'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Africa/Algiers'
USE_I18N = True
USE_TZ   = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.global_context',
            ],
        },
    },
]

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

SESSION_COOKIE_AGE      = 1800
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_HTTPONLY    = True
X_FRAME_OPTIONS         = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

EMAIL_BACKEND       = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST          = env('EMAIL_HOST',     default='smtp.gmail.com')
EMAIL_PORT          = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS       = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER     = env('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = env('DEFAULT_FROM_EMAIL',  default='GestiFlow <noreply@gestiflow.dz>')

GESTIFLOW = {
    'NOM_ENTREPRISE': env('NOM_ENTREPRISE', default='Mon Entreprise'),
    'ADRESSE':  env('ADRESSE',  default=''),
    'TELEPHONE': env('TELEPHONE', default=''),
    'EMAIL':    env('EMAIL',    default=''),
    'DEVISE':   env('DEVISE',   default='DA'),
    'TVA_DEFAUT': env('TVA_DEFAUT', default='19'),
    'STOCK_ALERTE_DEFAUT': env('STOCK_ALERTE_DEFAUT', default='5'),
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL          = '/auth/connexion/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/connexion/'
