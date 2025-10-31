#!/bin/bash

# Script d'entrée Docker pour la Plateforme de Révision Intelligente
# Projet de soutenance de mémoire - Niveau XXL

set -e

# Fonction pour afficher les messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Fonction pour attendre que la base de données soit prête
wait_for_db() {
    log "Attente de la base de données..."
    
    if [ "$DB_ENGINE" = "django.db.backends.postgresql" ]; then
        until python manage.py dbshell --database=default 2>/dev/null; do
            log "Base de données non disponible, attente..."
            sleep 2
        done
        log "Base de données prête !"
    fi
}

# Fonction pour attendre que Redis soit prêt
wait_for_redis() {
    log "Attente de Redis..."
    
    until python -c "import redis; redis.Redis.from_url('$REDIS_URL').ping()" 2>/dev/null; do
        log "Redis non disponible, attente..."
        sleep 2
    done
    log "Redis prêt !"
}

# Fonction pour exécuter les migrations
run_migrations() {
    log "Exécution des migrations..."
    python manage.py migrate --noinput
    log "Migrations terminées !"
}

# Fonction pour collecter les fichiers statiques
collect_static() {
    log "Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
    log "Fichiers statiques collectés !"
}

# Fonction pour créer un super utilisateur si nécessaire
create_superuser() {
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        log "Création du super utilisateur..."
        python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Super utilisateur créé avec succès !')
else:
    print('Super utilisateur existe déjà.')
"
    fi
}

# Fonction pour vérifier la santé de l'application
health_check() {
    log "Vérification de la santé de l'application..."
    
    # Vérifier que Django peut démarrer
    python manage.py check --deploy
    
    # Vérifier la base de données
    python manage.py dbshell --database=default -c "SELECT 1;" > /dev/null 2>&1
    
    log "Application en bonne santé !"
}

# Fonction principale
main() {
    log "Démarrage de la Plateforme de Révision Intelligente..."
    
    # Attendre les services
    wait_for_db
    # Fonction pour attendre que Redis soit prêt
wait_for_redis() {
    log "Attente de Redis..."
    
    # Timeout de 30 secondes maximum
    local timeout=30
    local counter=0
    
    while [ $counter -lt $timeout ]; do
        if python -c "import redis; redis.Redis.from_url('$REDIS_URL').ping()" 2>/dev/null; then
            log "Redis prêt !"
            return 0
        fi
        log "Redis non disponible, attente... ($((timeout - counter)) secondes restantes)"
        sleep 2
        counter=$((counter + 2))
    done
    
    log "ATTENTION: Redis non disponible après $timeout secondes, continuation sans Redis"
    return 1
}
    
    # Initialisation
    run_migrations
    collect_static
    create_superuser
    
    # Vérification finale
    health_check
    
    log "Initialisation terminée !"
    
    # Exécuter la commande passée
    exec "$@"
}

# Gestion des signaux
trap 'log "Arrêt de l'\''application..."; exit 0' SIGTERM SIGINT

# Lancer la fonction principale
main "$@"
