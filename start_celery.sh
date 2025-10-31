#!/bin/bash

echo "🚀 Démarrage de Celery pour SmartEtude"
echo "======================================"

# Activer l'environnement virtuel
source .venv/bin/activate

# Vérifier que Redis est en cours d'exécution
echo "🔍 Vérification de Redis..."
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis n'est pas en cours d'exécution. Démarrage..."
    redis-server --daemonize yes
    sleep 2
fi

# Démarrer Celery Worker
echo "👷 Démarrage du worker Celery..."
celery -A fiches_revision worker --loglevel=info --concurrency=4 &

# Démarrer Celery Beat (planificateur)
echo "⏰ Démarrage de Celery Beat..."
celery -A fiches_revision beat --loglevel=info &

echo "✅ Celery démarré avec succès !"
echo ""
echo "📊 Pour monitorer les tâches:"
echo "celery -A fiches_revision flower"
echo ""
echo "🛑 Pour arrêter Celery:"
echo "pkill -f celery"
