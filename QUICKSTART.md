# 🚀 Guide de Démarrage Rapide - SmartEtude

## ⚡ Démarrage Ultra-Rapide

### 1. **Démarrage en une commande**
```bash
./start_dev.sh
```

### 2. **Ou démarrage manuel**
```bash
# Activation de l'environnement virtuel
source .venv/bin/activate

# Démarrage avec configuration simplifiée
python manage_simple.py runserver 0.0.0.0:8000
```

## 🌐 Accès à l'Application

- **Page d'accueil**: http://localhost:8000/
- **Interface admin**: http://localhost:8000/admin/
- **Vue de test**: http://localhost:8000/test/
- **Dashboard**: http://localhost:8000/dashboard/

## 🔑 Identifiants de Connexion

- **Utilisateur**: `admin`
- **Mot de passe**: `admin123`

## 🛠️ Commandes Utiles

### **Vérification de l'état**
```bash
python manage_simple.py check
```

### **Création d'un superutilisateur**
```bash
python manage_simple.py createsuperuser
```

### **Construction des assets CSS**
```bash
npm run build:css
```

### **Migrations de base de données**
```bash
python manage_simple.py makemigrations
python manage_simple.py migrate
```

## 📁 Structure du Projet

```
fiches_revision/
├── core/                 # Application principale
├── analytics/            # Analytics et statistiques
├── ai_engine/            # Moteur d'intelligence artificielle
├── gamification/         # Système de gamification
├── templates/            # Templates HTML
├── static/               # Fichiers statiques (CSS, JS)
├── fiches_revision/      # Configuration Django
│   ├── settings.py       # Configuration complète
│   └── settings_simple.py # Configuration simplifiée
└── manage_simple.py      # Script de gestion simplifié
```

## 🔧 Configuration

### **Configuration Simplifiée (Recommandée pour le développement)**
- Fichier: `fiches_revision/settings_simple.py`
- Utilise: `manage_simple.py`
- Fonctionnalités: Base Django + modèles locaux

### **Configuration Complète (Production)**
- Fichier: `fiches_revision/settings.py`
- Utilise: `manage.py`
- Fonctionnalités: Toutes les fonctionnalités avancées

## 🚨 Résolution de Problèmes

### **Erreur de middleware ou ALLOWED_HOSTS**
Si vous avez des erreurs de middleware ou d'ALLOWED_HOSTS, utilisez la configuration simplifiée :
```bash
DJANGO_SETTINGS_MODULE=fiches_revision.settings_simple python manage.py runserver
```

### **Erreur DisallowedHost**
Si vous avez l'erreur "Invalid HTTP_HOST header", la configuration simplifiée accepte tous les hôtes (`ALLOWED_HOSTS = ['*']`).

### **Erreur de base de données**
```bash
# Supprimer la base existante
rm db.sqlite3

# Recréer les migrations
rm -rf */migrations/
python manage_simple.py makemigrations
python manage_simple.py migrate

# Créer un superutilisateur
python manage_simple.py createsuperuser
```

### **Problèmes de dépendances**
```bash
pip install -r requirements.txt
npm install
```

## 📚 Documentation Complète

Pour plus de détails, consultez le fichier `README.md` principal.

## 🎯 Prochaines Étapes

1. **Explorer l'interface admin** pour créer du contenu
2. **Tester l'upload de cours** via l'interface
3. **Créer des quiz** et des questions
4. **Personnaliser l'interface** avec Tailwind CSS

---

**🎓 SmartEtude - Plateforme de révision intelligente**
**✨ Intelligence artificielle et gamification pour l'apprentissage**
