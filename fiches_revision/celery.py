"""
Configuration Celery pour SmartEtude
"""

import os
from celery import Celery

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fiches_revision.settings')

app = Celery('fiches_revision')

# Configuration depuis les settings Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découverte automatique des tâches
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
