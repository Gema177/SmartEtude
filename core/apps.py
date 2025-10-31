from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Import des signaux pour activer la politique de session unique
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Ne jamais casser le démarrage si l'import échoue
            pass
