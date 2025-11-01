#!/bin/bash
set -e

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

wait_for_db() {
    log "Attente de la base de données..."
    sleep 10
    log "Continuation avec la base de données..."
}

run_migrations() {
    log "Exécution des migrations..."
    python manage.py migrate --noinput
    log "Migrations terminées !"
}

collect_static() {
    log "Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
    log "Fichiers statiques collectés !"
}

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

health_check() {
    log "Vérification de la santé de l'application..."
    python manage.py check --deploy
    log "Application en bonne santé !"
}

main() {
    log "Démarrage de la Plateforme de Révision Intelligente..."
    wait_for_db
    run_migrations
    collect_static
    create_superuser
    health_check
    log "Initialisation terminée !"
    log "Démarrage de Gunicorn..."
    exec gunicorn smartetude.wsgi:application --bind 0.0.0.0:10000 --workers 3
}

main "$@"