from django.apps import AppConfig


class GamificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gamification'
    
    def ready(self):
        """Enregistre les signaux lors du chargement de l'application"""
        import gamification.signals