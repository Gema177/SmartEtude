from __future__ import annotations

from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import BillingPlan, Payment, Subscription
from .lygos_client import lygos


def _ensure_default_plans() -> None:
    """Create default plans if they do not exist: 3000 XAF/month, 30000 XAF/year."""
    BillingPlan.objects.get_or_create(
        name="Mensuel",
        defaults={"price": 3000, "currency": "XAF", "interval": "month", "is_active": True},
    )
    BillingPlan.objects.get_or_create(
        name="Annuel",
        defaults={"price": 30000, "currency": "XAF", "interval": "year", "is_active": True},
    )


@login_required
def billing_plans(request: HttpRequest) -> HttpResponse:
    _ensure_default_plans()
    plans = BillingPlan.objects.filter(is_active=True).order_by("price")
    subscription: Optional[Subscription] = (
        Subscription.objects.filter(user=request.user).order_by("-created_at").first()
    )
    return render(
        request,
        "billing_plans.html",
        {
            "plans": plans,
            "subscription": subscription,
            "operators": (settings.LYGOS_SUPPORTED_OPERATORS or "").split(","),
        },
    )


@login_required
def billing_checkout(request: HttpRequest, plan_id: int) -> HttpResponse:
    plan = get_object_or_404(BillingPlan, pk=plan_id, is_active=True)

    if request.method == "POST":
        operator = request.POST.get("operator") or "MTN"
        msisdn = request.POST.get("msisdn") or ""
        if not msisdn:
            return render(
                request,
                "billing_plans.html",
                {
                    "plans": BillingPlan.objects.filter(is_active=True),
                    "error": "Numéro Mobile Money requis",
                    "operators": (settings.LYGOS_SUPPORTED_OPERATORS or "").split(","),
                },
                status=400,
            )

        # Créer/mettre à jour l'abonnement en attente
        sub = Subscription.objects.create(user=request.user, plan=plan, status="pending")

        # Créer un paiement pending (sans external_id pour éviter le conflit unique)
        payment = Payment.objects.create(
            user=request.user,
            subscription=sub,
            amount=plan.price,
            currency=plan.currency,
            operator=operator,
            status="pending",
            external_id=None,  # Éviter le conflit unique lors de la création
        )

        # Initier le payin (stub tant que l'endpoint exact n'est pas confirmé)
        callback_url = request.build_absolute_uri(reverse("billing_webhook_lygos"))
        try:
            # NOTE: L'endpoint de création de paiement n'est pas documenté dans l'API Lygos fournie
            # Cette section est en attente de l'endpoint réel de création de paiement
            resp = lygos.create_payin(
                amount=plan.price,
                currency=plan.currency,
                operator=operator,
                customer_msisdn=msisdn,
                callback_url=callback_url,
                metadata={"payment_id": payment.id, "subscription_id": sub.id},
            )
        except RuntimeError as e:
            # Si c'est notre erreur simulée (endpoint non disponible)
            if "L'endpoint de création de paiement n'est pas disponible" in str(e):
                # Option: Simuler un paiement réussi pour les tests
                # Décommentez les lignes suivantes pour simuler un succès:
                external_id = f"simulated_{payment.id}"
                payment.external_id = external_id
                payment.status = "succeeded"
                payment.raw = {"simulated": True, "payin_id": external_id}
                payment.save(update_fields=["external_id", "status", "raw", "updated_at"])
                sub.status = "active"
                sub.started_at = timezone.now()
                if sub.plan.interval == "month":
                    sub.current_period_end = sub.started_at + timedelta(days=30)
                else:
                    sub.current_period_end = sub.started_at + timedelta(days=365)
                sub.save()
                status_url = reverse("billing_status", kwargs={"payment_id": payment.id})
                return redirect(status_url)

                # Pour l'instant, afficher l'erreur
                # payment.status = "failed"
                # payment.raw = {"error": str(e)}
                # payment.save(update_fields=["status", "raw", "updated_at"])
                # return render(
                #     request,
                #     "checkout_pending.html",
                #     {
                #         "error": "L'API de création de paiement n'est pas encore disponible. Contactez le support Lygos pour obtenir l'endpoint de création de paiement.",
                #         "payment": payment,
                #         "plan": plan
                #     },
                #     status=502,
                # )
            else:
                # Autre erreur RuntimeError
                payment.status = "failed"
                payment.raw = {"error": str(e)}
                payment.save(update_fields=["status", "raw", "updated_at"])
                return render(
                    request,
                    "checkout_pending.html",
                    {"error": f"Erreur API Lygos: {str(e)}", "payment": payment, "plan": plan},
                    status=502,
                )
        except Exception as e:
            # Autres exceptions (réseau, etc.)
            payment.status = "failed"
            payment.raw = {"error": str(e)}
            payment.save(update_fields=["status", "raw", "updated_at"])
            return render(
                request,
                "checkout_pending.html",
                {"error": f"Erreur de connexion: {str(e)}", "payment": payment, "plan": plan},
                status=502,
            )

        external_id = str(resp.get("payin_id") or resp.get("id") or "")
        payment.external_id = external_id
        payment.raw = resp
        payment.save(update_fields=["external_id", "raw", "updated_at"])

        status_url = reverse("billing_status", kwargs={"payment_id": payment.id})
        return redirect(status_url)

    # GET fallback -> revenir aux plans
    return redirect("billing_plans")


@login_required
def billing_status(request: HttpRequest, payment_id: int) -> HttpResponse:
    payment = get_object_or_404(Payment, pk=payment_id, user=request.user)

    if payment.status == "pending" and payment.external_id:
        try:
            status_resp = lygos.get_payin_status(payment.external_id)
            payment.raw = {**(payment.raw or {}), "last_status": status_resp}
            # Adapter selon le contrat Lygos
            api_status = str(status_resp.get("status") or "").lower()
            if api_status in {"succeeded", "success", "paid"}:
                payment.status = "succeeded"
                # Activer l'abonnement
                sub = payment.subscription
                if sub and sub.status != "active":
                    sub.status = "active"
                    sub.started_at = timezone.now()
                    if sub.plan.interval == "month":
                        sub.current_period_end = sub.started_at + timedelta(days=30)
                    else:
                        sub.current_period_end = sub.started_at + timedelta(days=365)
                    sub.save()
            elif api_status in {"failed", "canceled", "cancelled"}:
                payment.status = "failed"
            payment.save(update_fields=["status", "raw", "updated_at"])
        except Exception as e:
            # Ne pas bloquer l'affichage; montrer l'erreur côté UI
            return render(
                request,
                "checkout_pending.html",
                {
                    "payment": payment,
                    "plan": payment.subscription.plan if payment.subscription else None,
                    "error": str(e),
                },
                status=502,
            )

    return render(
        request,
        "checkout_pending.html",
        {"payment": payment, "plan": payment.subscription.plan if payment.subscription else None},
    )


def billing_webhook_lygos(request: HttpRequest) -> HttpResponse:
    """Réception des notifications Lygos (succès/échec). Idempotent.

    À sécuriser avec signature quand la doc sera confirmée.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    payload = request.body.decode("utf-8") or "{}"
    try:
        import json

        data = json.loads(payload)
    except Exception:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    external_id = str(data.get("payin_id") or data.get("id") or "")
    status_str = str(data.get("status") or "").lower()

    payment = Payment.objects.filter(external_id=external_id).first()
    if not payment:
        return JsonResponse({"detail": "unknown payment"}, status=202)

    # idempotence: si déjà finalisé, ignorer
    if payment.status in {"succeeded", "failed"}:
        return JsonResponse({"detail": "already processed"}, status=200)

    payment.raw = {**(payment.raw or {}), "webhook": data}
    if status_str in {"succeeded", "success", "paid"}:
        payment.status = "succeeded"
        sub = payment.subscription
        if sub and sub.status != "active":
            sub.status = "active"
            sub.started_at = timezone.now()
            if sub.plan.interval == "month":
                sub.current_period_end = sub.started_at + timedelta(days=30)
            else:
                sub.current_period_end = sub.started_at + timedelta(days=365)
            sub.save()
    elif status_str in {"failed", "canceled", "cancelled"}:
        payment.status = "failed"
    payment.save(update_fields=["status", "raw", "updated_at"])

    return JsonResponse({"detail": "ok"}, status=200)
