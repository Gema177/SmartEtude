#!/bin/bash

echo "🔧 Installation des dépendances pour l'extraction de texte"
echo "=================================================="

# Vérifier si pip est installé
if ! command -v pip &> /dev/null; then
    echo "❌ pip n'est pas installé. Veuillez installer Python et pip."
    exit 1
fi

echo "📦 Installation des packages Python..."

# Installer PyPDF2 pour les PDF
echo "📄 Installation de PyPDF2..."
pip install PyPDF2

# Installer python-docx pour les DOCX
echo "📝 Installation de python-docx..."
pip install python-docx

# Installer Pillow pour le traitement d'images (optionnel)
echo "🖼️  Installation de Pillow..."
pip install Pillow

echo ""
echo "✅ Installation terminée !"
echo ""
echo "🎯 Formats maintenant supportés:"
echo "- TXT: Extraction directe"
echo "- PDF: Extraction avec PyPDF2"
echo "- DOCX: Extraction avec python-docx"
echo "- DOC: Extraction avec python-docx"
echo ""
echo "🧪 Pour tester l'extraction:"
echo "python test_extraction.py"
