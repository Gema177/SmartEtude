#!/usr/bin/env bash
# Script de build pour Render

set -o errexit  # Exit on error

echo "Building application..."

# Installer les dépendances Python
pip install -r requirements.txt

# Installer les dépendances Node.js si nécessaire
if [ -f package.json ]; then
    npm install
    npm run build:css || echo "Warning: CSS build failed"
fi

echo "Build completed successfully!"

