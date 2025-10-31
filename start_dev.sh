#!/bin/bash

# =============================================================================
# SCRIPT DE DÉMARRAGE - SMARTETUDE
# =============================================================================
# Script pour démarrer l'environnement de développement

echo "🚀 Démarrage de SmartEtude..."
echo "📁 Répertoire: $(pwd)"
echo "🔧 Mode: Développement"
echo ""

# Vérification de l'environnement virtuel
if [ ! -d ".venv" ]; then
    echo "❌ Environnement virtuel non trouvé. Création..."
    python3 -m venv .venv
    echo "✅ Environnement virtuel créé"
fi

# Activation de l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source .venv/bin/activate

# Vérification des dépendances Python
echo "📦 Vérification des dépendances Python..."
if ! python -c "import django" 2>/dev/null; then
    echo "❌ Django non installé. Installation des dépendances..."
    pip install -r requirements.txt
    echo "✅ Dépendances installées"
else
    echo "✅ Dépendances Python OK"
fi

# Vérification des dépendances Node.js
echo "📦 Vérification des dépendances Node.js..."
if [ ! -d "node_modules" ]; then
    echo "❌ Modules Node.js non trouvés. Installation..."
    npm install
    echo "✅ Modules Node.js installés"
else
    echo "✅ Dépendances Node.js OK"
fi

# Construction des assets CSS
echo "🎨 Construction des assets CSS..."
npm run build:css
echo "✅ Assets CSS construits"

# Vérification de la configuration Django
echo "🔍 Vérification de la configuration Django..."
python manage_simple.py check
if [ $? -eq 0 ]; then
    echo "✅ Configuration Django OK"
else
    echo "❌ Erreur de configuration Django"
    exit 1
fi

# Nettoyage des processus existants sur le port 8000
echo "🧹 Nettoyage des processus existants..."
PORT=8000
PID=$(lsof -ti:$PORT 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "⚠️  Port $PORT occupé par le processus $PID. Arrêt..."
    kill -9 $PID 2>/dev/null
    sleep 2
    echo "✅ Port $PORT libéré"
else
    echo "✅ Port $PORT libre"
fi

# Vérification finale du port
sleep 1
if lsof -ti:$PORT >/dev/null 2>&1; then
    echo "❌ Impossible de libérer le port $PORT"
    echo "💡 Essayez de redémarrer votre terminal ou utilisez un autre port"
    exit 1
fi

# Démarrage du serveur
echo ""
echo "🚀 Démarrage du serveur Django..."
echo "📁 Configuration: fiches_revision/settings_simple.py"
echo "🌐 URL: http://localhost:8000"
echo "🔑 Admin: http://localhost:8000/admin"
echo "📚 API: http://localhost:8000/api/v1/"
echo ""
echo "💡 Utilisez Ctrl+C pour arrêter le serveur"
echo ""

# Démarrage du serveur avec gestion d'erreur
python manage_simple.py runserver 0.0.0.0:8000

# En cas d'erreur
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erreur lors du démarrage du serveur"
    echo "💡 Vérifiez que le port 8000 est libre et que Django est installé"
    echo "🔧 Essayez: lsof -ti:8000 | xargs kill -9"
    exit 1
fi
