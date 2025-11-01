from __future__ import annotations

from functools import wraps
from typing import Callable

from django.contrib import messages
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from .models import Subscription


def subscription_required(view_func: Callable) -> Callable:
    """Décorateur temporairement désactivé pour permettre l'accès sans abonnement.
    
    Toutes les fonctionnalités sont disponibles en version d'essai.
    """

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
            
        # Afficher un message indiquant que c'est une version d'essai
        messages.info(
            request,
            "Version d'essai - Toutes les fonctionnalités sont actuellement disponibles.",
        )
        
        return view_func(request, *args, **kwargs)

    return _wrapped_view
