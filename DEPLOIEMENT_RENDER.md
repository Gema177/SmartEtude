# Guide de Déploiement sur Render

## Configuration nécessaire

### 1. Variables d'environnement à configurer dans Render

Dans le dashboard Render, ajoutez ces variables d'environnement :

**Obligatoires :**
- `SECRET_KEY` : Clé secrète Django (générez-en une avec : `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`)
- `DJANGO_SETTINGS_MODULE` : `fiches_revision.settings`

**Optionnelles (mais recommandées) :**
- `DEBUG` : `false` (pour la production)
- `ALLOWED_HOSTS` : Votre domaine Render (ex: `votre-app.onrender.com`)
- `OPENAI_API_KEY` : Si vous utilisez les fonctionnalités IA
- `LYGOS_API_KEY` : Si vous utilisez les paiements

**Base de données :**
Si vous utilisez PostgreSQL sur Render :
- `DB_ENGINE` : `django.db.backends.postgresql`
- `DB_NAME` : Nom de votre base de données
- `DB_USER` : Utilisateur PostgreSQL
- `DB_PASSWORD` : Mot de passe PostgreSQL
- `DB_HOST` : Hôte PostgreSQL
- `DB_PORT` : Port PostgreSQL (généralement 5432)

### 2. Configuration du service web

- **Build Command** (si vous utilisez render.yaml, c'est géré automatiquement) :
  ```bash
  pip install -r requirements.txt && npm install && npm run build:css
  ```

- **Start Command** (déjà dans le Procfile) :
  ```bash
  python manage.py migrate && python manage.py collectstatic --noinput && gunicorn fiches_revision.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
  ```

### 3. Configuration automatique

Le fichier `settings.py` détecte automatiquement l'environnement Render grâce à la variable `RENDER_EXTERNAL_HOSTNAME` et configure :
- ✅ `DEBUG = False`
- ✅ `SECURE_SSL_REDIRECT = True`
- ✅ `SESSION_COOKIE_SECURE = True`
- ✅ `CSRF_COOKIE_SECURE = True`
- ✅ `ALLOWED_HOSTS` inclut automatiquement votre domaine Render

### 4. Résolution des problèmes

**Problème : "No open ports detected"**
- ✅ Solution : Utiliser le Procfile qui démarre Gunicorn avec `$PORT`

**Problème : Warnings de sécurité**
- ✅ Solution : Les paramètres de sécurité sont automatiquement activés sur Render

**Problème : Static files non trouvés**
- ✅ Solution : Le Procfile exécute `collectstatic --noinput` avant le démarrage

**Problème : Migrations non appliquées**
- ✅ Solution : Le Procfile exécute `migrate` avant le démarrage

### 5. Fichiers créés pour Render

- ✅ `Procfile` : Configuration du processus web
- ✅ `render.yaml` : Configuration optionnelle du service
- ✅ `requirements.txt` : Ajout de `gunicorn`
- ✅ `settings.py` : Configuration automatique pour Render

### 6. Notes importantes

- Le port est automatiquement géré par Render via la variable `$PORT`
- Les fichiers statiques sont servis par WhiteNoise (déjà configuré)
- Le secret key DOIT être changé en production (ne jamais utiliser la valeur par défaut)
- Toutes les migrations sont appliquées automatiquement au démarrage

