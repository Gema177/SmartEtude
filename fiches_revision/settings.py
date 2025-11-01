"""
Configuration Django pour SmartEtude

Ce fichier contient toutes les configurations nécessaires pour :
- Configuration de base Django
- Applications et middleware
- Base de données et cache
- Sécurité et authentification
- Configuration IA et API
- Monitoring et logging
"""

import os
from pathlib import Path
from datetime import timedelta
from decouple import config
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# =============================================================================
# CONFIGURATION DE BASE
# =============================================================================

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# SECURITY WARNING: keep the secret key used in production secret!
# En production, SECRET_KEY doit être défini via variable d'environnement
import secrets
import string

def generate_secret_key():
    """Génère une clé secrète aléatoire compatible Django"""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(50))

secret_key_default = config('SECRET_KEY', default=None)
if secret_key_default is None or (isinstance(secret_key_default, str) and secret_key_default.startswith('django-insecure-')):
    # Générer un secret key aléatoire si aucun n'est fourni
    SECRET_KEY = generate_secret_key()
    # Avertir si en production
    if os.environ.get('RENDER') or not DEBUG:
        import warnings
        warnings.warn(
            "SECRET_KEY généré automatiquement. Définissez SECRET_KEY dans les variables d'environnement pour la production!",
            UserWarning
        )
else:
    SECRET_KEY = secret_key_default

# Configuration ALLOWED_HOSTS
allowed_hosts_default = '127.0.0.1,localhost,0.0.0.0'
# Sur Render, ajouter automatiquement le domaine
render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_hostname:
    allowed_hosts_default += f',{render_hostname}'

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', 
    default=allowed_hosts_default, 
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# =============================================================================
# APPLICATIONS ET MIDDLEWARE
# =============================================================================

INSTALLED_APPS = [
    # Applications Django natives
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Applications tierces
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'django_extensions',
    'django_celery_beat',
    'django_celery_results',
    'oauth2_provider',
    'drf_spectacular',
    'debug_toolbar',
    
    # Applications locales
    'core',
    'api',
    'analytics',
    'ai_engine',
    'gamification',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'ratelimit.middleware.RatelimitMiddleware',  # Temporairement désactivé
]

# Activer la debug toolbar uniquement en développement
if DEBUG:
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    # IPs internes autorisées pour la toolbar
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]

# =============================================================================
# CONFIGURATION DES TEMPLATES ET URLS
# =============================================================================

ROOT_URLCONF = 'fiches_revision.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'fiches_revision.wsgi.application'

# =============================================================================
# BASE DE DONNÉES ET CACHE
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}

# Configuration du cache Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# =============================================================================
# VALIDATION DES MOTS DE PASSE
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =============================================================================
# INTERNATIONALISATION
# =============================================================================

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# =============================================================================
# FICHIERS STATIQUES ET MÉDIA
# =============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Configuration WhiteNoise pour servir les fichiers statiques en production
# Utiliser CompressedStaticFilesStorage au lieu de Manifest pour éviter les problèmes de manifest
# En développement, utiliser un storage simple sans compression
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    # Utiliser CompressedStaticFilesStorage sans manifest pour éviter les erreurs
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Configuration WhiteNoise
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG  # Recharger automatiquement en développement seulement

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Type de clé primaire par défaut
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# CONFIGURATION REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# =============================================================================
# CONFIGURATION JWT
# =============================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# =============================================================================
# CONFIGURATION CORS
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# =============================================================================
# CONFIGURATION CELERY
# =============================================================================

CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='django-db')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# =============================================================================
# CONFIGURATION IA (OpenAI)
# =============================================================================

OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
OPENAI_BASE_URL = config('OPENAI_BASE_URL', default='https://api.openai.com')
AI_MODEL = config('AI_MODEL', default='gpt-4o-mini')
AI_MAX_TOKENS = config('AI_MAX_TOKENS', default=800, cast=int)

# =============================================================================
# CONFIGURATION DES UPLOADS
# =============================================================================

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# =============================================================================
# PARAMÈTRES AUTH/SESSION
# =============================================================================

# URL de connexion/déconnexion
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = 'dashboard'
# Rediriger vers la page demandée après connexion si 'next' est dans l'URL
LOGOUT_REDIRECT_URL = 'home'

# Renforcer la gestion de session
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# Durée de vie des cookies de session (1 heure)
SESSION_COOKIE_AGE = 60 * 60
# Renouvelle l'expiration à chaque requête utilisateur
SESSION_SAVE_EVERY_REQUEST = True

# =============================================================================
# CONFIGURATION DE SÉCURITÉ
# =============================================================================

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Sécurité HTTPS (production)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)

# Détection automatique de l'environnement de production
if os.environ.get('RENDER'):
    # Sur Render, activer la sécurité HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    DEBUG = False

# =============================================================================
# PAIEMENTS LYGOS (Mobile Money)
# =============================================================================

LYGOS_BASE_URL = config('LYGOS_BASE_URL', default='https://api.lygosapp.com/v1/')
LYGOS_API_KEY = config('LYGOS_API_KEY', default='')
# Opérateurs pris en charge (ex: MTN, AIRTEL CONGO)
LYGOS_SUPPORTED_OPERATORS = config('LYGOS_SUPPORTED_OPERATORS', default='MTN,AIRTEL_CONGO')
LYGOS_WEBHOOK_SECRET = config('LYGOS_WEBHOOK_SECRET', default='')

# =============================================================================
# CONFIGURATION DU LOGGING
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'ai_engine': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# =============================================================================
# CONFIGURATION SENTRY (MONITORING)
# =============================================================================

if not DEBUG:
    sentry_sdk.init(
        dsn=config('SENTRY_DSN', default=''),
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True
    )

# =============================================================================
# CONFIGURATION DE L'API DOCUMENTATION
# =============================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'Plateforme de Révision Intelligente API',
    'DESCRIPTION': 'API complète pour la plateforme de révision avec IA',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
}

# =============================================================================
# CONFIGURATION DU RATE LIMITING
# =============================================================================

RATELIMIT_USE_CACHE = 'default'
RATELIMIT_ENABLE = True

# =============================================================================
# CONFIGURATION DES DIRECTORIES
# =============================================================================

# Créer le répertoire des logs s'il n'existe pas
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
