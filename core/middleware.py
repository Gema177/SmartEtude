"""
Middleware personnalisé pour gérer les sessions corrompues
"""
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.base import SessionBase
import logging

logger = logging.getLogger(__name__)


class CleanCorruptedSessionsMiddleware:
    """
    Middleware qui nettoie automatiquement les sessions corrompues
    S'exécute APRÈS SessionMiddleware pour avoir accès à request.session
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier si la session existe et si elle est corrompue
        if hasattr(request, 'session'):
            session_key = getattr(request.session, 'session_key', None)
            if session_key:
                # Vérifier directement dans la DB si la session peut être décodée
                try:
                    session_obj = Session.objects.get(session_key=session_key)
                    # Essayer de décoder la session
                    session_obj.get_decoded()
                except Session.DoesNotExist:
                    # Session n'existe pas en DB, créer une nouvelle
                    request.session.flush()
                    request.session.create()
                except Exception as e:
                    # Session corrompue - la supprimer de la DB et créer une nouvelle
                    logger.warning(f"Session corrompue détectée: {session_key}, suppression...")
                    try:
                        Session.objects.filter(session_key=session_key).delete()
                    except Exception:
                        pass
                    # Forcer la création d'une nouvelle session
                    request.session.flush()
                    request.session.create()

        response = self.get_response(request)
        return response
