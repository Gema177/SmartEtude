FROM python:3.10-slim

# Prevents Python from writing .pyc files and enables unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (for Pillow, psycopg, Node.js, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Leverage layer caching for deps
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies and build Tailwind CSS
COPY package.json package-lock.json* tailwind.config.js postcss.config.js* /app/
COPY static/src/ /app/static/src/
RUN if [ -f package.json ]; then npm install && npm run build:css || true; fi

# Copy project
COPY . /app/

EXPOSE 8000

# Default CMD: build CSS, apply migrations, collect static, clear corrupted sessions, then start gunicorn
CMD ["/bin/sh", "-c", "npm run build:css || true && python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py shell -c \"from django.contrib.sessions.models import Session; Session.objects.all().delete()\" && gunicorn fiches_revision.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
