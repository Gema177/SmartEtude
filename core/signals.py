from __future__ import annotations

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.sessions.models import Session


@receiver(user_logged_in)
def enforce_single_session(sender, request, user, **kwargs):
    """
    Enforce a single active session per user:
    - When a user logs in, delete all other sessions belonging to this user,
      keeping only the current session.
    """
    if not request or not hasattr(request, "session"):
        return

    current_key = request.session.session_key
    # Ensure current session key exists
    if not current_key:
        request.session.save()
        current_key = request.session.session_key

    # Iterate over all sessions and remove other sessions for this user
    # Also delete corrupted sessions (can't be decoded)
    for session in Session.objects.all():
        try:
            data = session.get_decoded()
            # If session is for this user and not the current one, delete it
            if data.get("_auth_user_id") == str(user.id) and session.session_key != current_key:
                try:
                    session.delete()
                except Exception:
                    # Never block login because of a deletion error
                    pass
        except Exception:
            # Session is corrupted (can't decode), delete it
            try:
                session.delete()
            except Exception:
                pass
