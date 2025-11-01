# =============================================================================
# DOCKERFILE - SMARTETUDE
# =============================================================================
# Image de base optimisée pour Django
FROM python:3.11-slim

# =============================================================================
# MÉTADONNÉES
# =============================================================================
LABEL maintainer="NDOUMBA DUVET GEMA <ndoumbaduvetgema@gmail.com>"
LABEL version="1.0.0"
LABEL description="SmartEtude - Plateforme de révision intelligente avec IA"

# =============================================================================
# VARIABLES D'ENVIRONNEMENT
# =============================================================================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DJANGO_SETTINGS_MODULE=fiches_revision.settings \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# =============================================================================
# INSTALLATION DES PAQUETS SYSTÈME
# =============================================================================
RUN apt-get update && apt-get install -y \
    # Outils de base
    curl \
    wget \
    git \
    vim \
    nano \
    # Dépendances Python
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    # Outils de développement
    nodejs \
    npm \
    # Nettoyage
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# CRÉATION DE L'UTILISATEUR NON-ROOT
# =============================================================================
RUN groupadd -r appuser && useradd -r -g appuser appuser

# =============================================================================
# CONFIGURATION DU RÉPERTOIRE DE TRAVAIL
# =============================================================================
WORKDIR /app

# =============================================================================
# INSTALLATION DES DÉPENDANCES PYTHON
# =============================================================================
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# =============================================================================
# INSTALLATION DES DÉPENDANCES NODE.JS
# =============================================================================
# INSTALLATION DES DÉPENDANCES NODE.JS
# =============================================================================
COPY package*.json /app/
COPY tailwind.config.js postcss.config.js /app/
RUN npm install && npm cache clean --force

# =============================================================================
# COPIE DES FICHIERS STATIQUES POUR TAILWIND
# =============================================================================
COPY static/ /app/static/

# =============================================================================
# BUILD TAILWIND CSS
# =============================================================================
RUN npm run build:css

# =============================================================================
# COPIE DU RESTE DU CODE
# =============================================================================
COPY . /app/
# =============================================================================
# COPIE DU CODE SOURCE


# =============================================================================
# CONFIGURATION DES PERMISSIONS
# =============================================================================
RUN chown -R appuser:appuser /app && \
    chmod +x /app/docker-entrypoint.sh

# =============================================================================
# CRÉATION DES RÉPERTOIRES NÉCESSAIRES
# =============================================================================
RUN mkdir -p /app/logs /app/media /app/staticfiles && \
    chown -R appuser:appuser /app/logs /app/media /app/staticfiles

# =============================================================================
# CONFIGURATION DE LA SANTÉ
# =============================================================================
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# =============================================================================
# CONFIGURATION DES PORTS
# =============================================================================
EXPOSE 10000

# =============================================================================
# CHANGEMENT D'UTILISATEUR
# =============================================================================
USER appuser

# =============================================================================
# POINT D'ENTRÉE
# =============================================================================
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# =============================================================================
# COMMANDE PAR DÉFAUT
# =============================================================================
CMD ["gunicorn", "fiches_revision.wsgi:application", "--bind", "0.0.0.0:10000", "--workers", "2", "--timeout", "120"]