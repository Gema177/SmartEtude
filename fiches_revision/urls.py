"""
URLs principales pour SmartEtude

Ce fichier définit la structure des URLs de l'application :
- Interface d'administration
- API REST v1
- Applications principales
- Authentification
- Documentation API
- Fichiers statiques et média
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView, 
    SpectacularSwaggerView, 
    SpectacularRedocView
)

# =============================================================================
# CONFIGURATION DE L'ADMIN DJANGO

admin.site.site_header = "🎓 SmartEtude - Administration"
admin.site.site_title = "Admin - SmartEtude"
admin.site.index_title = "Tableau de bord de SmartEtude"

# =============================================================================
# PATTERNS D'URLS PRINCIPAUX
# =============================================================================

urlpatterns = [
    # =====================================================================
    # INTERFACE D'ADMINISTRATION
    # =====================================================================
    path('admin/', admin.site.urls),
    
    # =====================================================================
    # API REST V1
    # =====================================================================
    path('api/v1/', include('api.urls')),
    
    # =====================================================================
    # APPLICATIONS PRINCIPALES
    # =====================================================================
    path('', include('core.urls')),                    # Application principale
    path('analytics/', include('analytics.urls')),     # Analytics et statistiques
    path('ai/', include('ai_engine.urls')),            # Moteur IA
    path('gamification/', include('gamification.urls')), # Système de gamification
    
    # =====================================================================
    # AUTHENTIFICATION ET COMPTES
    # =====================================================================
    path('accounts/', include('django.contrib.auth.urls')),
    
    # =====================================================================
    # DOCUMENTATION DE L'API
    # =====================================================================
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # =====================================================================
    # REDIRECTION DE LA RACINE
    # =====================================================================
    path('', RedirectView.as_view(url='/', permanent=False), name='home-redirect'),
]

# =============================================================================
# CONFIGURATION DES FICHIERS STATIQUES ET MÉDIA (DÉVELOPPEMENT)
# =============================================================================

if settings.DEBUG:
    # Fichiers média (uploads utilisateur)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Fichiers statiques (CSS, JS, images)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar (chargée uniquement en DEV)
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# =============================================================================
# CONFIGURATION DES HANDLERS D'ERREUR (PRODUCTION)
# =============================================================================

# Ces handlers peuvent être configurés pour la production
# handler404 = 'core.views.handler404'
# handler500 = 'core.views.handler500'
# handler403 = 'core.views.handler403'
