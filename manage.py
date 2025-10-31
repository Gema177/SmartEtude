#!/usr/bin/env python
"""
Script de gestion Django pour SmartEtude

Ce script permet d'exécuter les commandes Django de gestion :
- python manage.py runserver
- python manage.py migrate
- python manage.py createsuperuser
- python manage.py collectstatic
- etc.
"""

import os
import sys
import warnings
from pathlib import Path

# =============================================================================
# CONFIGURATION DE L'ENVIRONNEMENT
# =============================================================================

def setup_environment():
    """Configure l'environnement Django"""
    # Désactiver les avertissements de dépréciation
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # Vérifier que Django est installé
    try:
        import django
    except ImportError:
        print("❌ Erreur: Django n'est pas installé.")
        print("💡 Installez Django avec: pip install django")
        sys.exit(1)
    
    # Vérifier la version de Python
    if sys.version_info < (3, 8):
        print("❌ Erreur: Python 3.8+ est requis.")
        print(f"💡 Version actuelle: {sys.version}")
        sys.exit(1)
    
    # Vérifier que le projet est dans le PYTHONPATH
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def main():
    """Fonction principale du script manage.py"""
    try:
        # Configuration de l'environnement
        setup_environment()
        
        # Configuration Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fiches_revision.settings')
        
        # Import et exécution de Django
        from django.core.management import execute_from_command_line
        
        # Exécution de la commande
        execute_from_command_line(sys.argv)
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Vérifiez que toutes les dépendances sont installées:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        print("💡 Vérifiez la configuration du projet")
        sys.exit(1)

# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == '__main__':
    main()
