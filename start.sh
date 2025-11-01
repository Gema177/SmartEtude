#!/usr/bin/env bash
# Script de démarrage pour Render avec gestion d'erreurs

set -e  # Arrêter sur erreur

echo "=== Démarrage de SmartEtude ==="

# Vérifier que Python est disponible
python --version

# Vérifier la configuration Django
echo "Vérification de la configuration Django..."
python manage.py check --deploy || {
    echo "WARNING: Django check a trouvé des problèmes, mais on continue..."
}

# Appliquer les migrations
echo "Application des migrations..."
python manage.py migrate --noinput || {
    echo "ERREUR: Les migrations ont échoué"
    exit 1
}

# Build des assets CSS avant collectstatic
echo "Build des assets CSS..."
if [ -f package.json ]; then
    if [ ! -d "node_modules" ]; then
        echo "Installation des dépendances Node.js..."
        npm install
    fi
    echo "Compilation du CSS..."
    npm run build:css || {
        echo "WARNING: Le build CSS a échoué, mais on continue..."
    }
fi

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput || {
    echo "WARNING: collectstatic a échoué, mais on continue..."
}

# Démarrer Gunicorn
echo "Démarrage de Gunicorn sur le port $PORT..."
exec gunicorn fiches_revision.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload

