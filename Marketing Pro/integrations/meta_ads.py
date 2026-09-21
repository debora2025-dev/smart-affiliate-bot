"""Conector Meta (Facebook + Instagram) via Graph API — Lead Ads e Insights.

Requer um token de acesso de sistema (System User Token) com os escopos
`leads_retrieval`, `ads_read` e `pages_read_engagement`, gerado no Meta Business
Suite (business.facebook.com > Configurações do negócio > Usuários do sistema).

Variáveis de ambiente:
    META_ACCESS_TOKEN   - token de acesso de longa duração
    META_AD_ACCOUNT_ID  - id da conta de anúncios, formato "act_123456789"
    META_PAGE_ID        - id da página (para leads de formulários instantâneos)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from .base import Lead, LeadSource

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class MetaAdsSource(LeadSource):
    platform_key = "meta"
    display_name = "Meta (Facebook & Instagram)"

    def is_configured(self) -> bool:
        return bool(self.config.get("META_ACCESS_TOKEN") and self.config.get("META_AD_ACCOUNT_ID"))

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = dict(params or {})
        params["access_token"] = self.config["META_ACCESS_TOKEN"]
        response = requests.get(f"{GRAPH_API_BASE}/{path}", params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    def fetch_leads(self, limit: int = 50) -> list[Lead]:
        ad_account_id = self.config["META_AD_ACCOUNT_ID"]
        data = self._get(
            f"{ad_account_id}/leadgenforms",
            {"fields": "id,name,leads_count", "limit": limit},
        )
        leads: list[Lead] = []
        for form in data.get("data", []):
            form_leads = self._get(f"{form['id']}/leads", {"limit": limit})
            for raw in form_leads.get("data", []):
                field_values = {f["name"]: f["values"][0] for f in raw.get("field_data", [])}
                leads.append(
                    Lead(
                        id=f"meta_{raw['id']}",
                        platform="meta",
                        name=field_values.get("full_name", field_values.get("nome", "")),
                        email=field_values.get("email", ""),
                        phone=field_values.get("phone_number", field_values.get("telefone", "")),
                        campaign=form.get("name", "Formulário Meta"),
                        created_at=datetime.fromisoformat(raw["created_time"].replace("+0000", "+00:00")),
                        source_raw=raw,
                    )
                )
        return leads

    def fetch_campaign_metrics(self) -> dict[str, Any]:
        ad_account_id = self.config["META_AD_ACCOUNT_ID"]
        data = self._get(
            f"{ad_account_id}/insights",
            {"fields": "impressions,clicks,spend,actions", "date_preset": "last_30d"},
        )
        row = (data.get("data") or [{}])[0]
        return {
            "impressions": int(row.get("impressions", 0)),
            "clicks": int(row.get("clicks", 0)),
            "spend": float(row.get("spend", 0.0)),
        }
