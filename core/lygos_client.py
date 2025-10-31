from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class LygosClient:
    """Client HTTP minimal pour l'API Lygos.

    REMARQUE: La doc fournie expose surtout la liste des gateways et le statut
    des payins. L'endpoint d'initiation de payin n'est pas détaillé ici.
    Cette classe est conçue pour être étendue facilement quand vous aurez
    l'URL/contract exacts de "create payin".
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "LYGOS_API_KEY", "")
        self.base_url = (base_url or getattr(settings, "LYGOS_BASE_URL", "https://api.lygosapp.com/v1/")).rstrip("/")
        if not self.api_key:
            logger.warning("LYGOS_API_KEY manquant - configurez-le dans .env")

    def _headers(self) -> Dict[str, str]:
        return {
            "api-key": self.api_key,  # Lygos utilise api-key au lieu de Authorization Bearer
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def list_gateways(self) -> Dict[str, Any]:
        url = f"{self.base_url}/gateway"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        self._raise_for_status(resp)
        return resp.json()

    def get_gateway(self, gateway_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/gateway/{gateway_id}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        self._raise_for_status(resp)
        return resp.json()

    def get_payin_status(self, payin_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/payin/{payin_id}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        self._raise_for_status(resp)
        return resp.json()

    # Placeholder: à adapter lorsque l'endpoint de création de payin sera connu
    def create_payin(self, *, amount: int, currency: str, operator: str, customer_msisdn: str, callback_url: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initie un paiement Mobile Money.

        Retour attendu (exemple): {"payin_id": "...", "status": "pending", ...}

        NOTE: Cette méthode est en attente de l'endpoint réel de création de paiement Lygos.
        L'endpoint /payin n'est pas documenté dans l'API fournie.
        """
        # Pour l'instant, simuler une erreur pour indiquer que l'endpoint n'existe pas
        raise RuntimeError(
            "L'endpoint de création de paiement n'est pas disponible dans la documentation Lygos. "
            "Contactez le support Lygos pour obtenir l'endpoint POST /payin ou équivalent. "
            f"URL tentée: {self.base_url}/payin"
        )

    @staticmethod
    def _raise_for_status(resp: requests.Response) -> None:
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RuntimeError(f"Lygos API error {resp.status_code}: {detail}")


lygos = LygosClient()
