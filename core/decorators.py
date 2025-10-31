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
    """Vérifie qu'un utilisateur possède un abonnement actif.

    Redirige vers la page des plans avec un message sinon.
    """

    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            # Laisser @login_required gérer la redirection
            return view_func(request, *args, **kwargs)
        now = timezone.now()
        has_active = (
            Subscription.objects.filter(user=request.user, status="active")
            .filter(models.Q(current_period_end__isnull=True) | models.Q(current_period_end__gt=now))
            .exists()
        )
        if not has_active:
            messages.warning(request, "Vous devez avoir un abonnement actif pour accéder à cette fonctionnalité.")
            return redirect(reverse("billing_plans"))
        return view_func(request, *args, **kwargs)

    return _wrapped
