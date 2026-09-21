"""Conector TikTok — Instant Forms via TikTok Business API (REST).

Requer um app aprovado no TikTok for Business Developer Portal e um
access token gerado via OAuth (Authorization Code flow).
Ver: https://business-api.tiktok.com/portal/docs?id=1739940107331586

Variáveis de ambiente:
    TIKTOK_ACCESS_TOKEN
    TIKTOK_ADVERTISER_ID
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from .base import Lead, LeadSource

TIKTOK_API_BASE = "https://business-api.tiktok.com/open_api/v1.3"


class TikTokAdsSource(LeadSource):
    platform_key = "tiktok"
    display_name = "TikTok Ads"

    def is_configured(self) -> bool:
        return bool(self.config.get("TIKTOK_ACCESS_TOKEN") and self.config.get("TIKTOK_ADVERTISER_ID"))

    def _headers(self) -> dict[str, str]:
        return {"Access-Token": self.config["TIKTOK_ACCESS_TOKEN"]}

    def fetch_leads(self, limit: int = 50) -> list[Lead]:
        advertiser_id = self.config["TIKTOK_ADVERTISER_ID"]
        response = requests.get(
            f"{TIKTOK_API_BASE}/page/leads/get/",
            headers=self._headers(),
            params={"advertiser_id": advertiser_id, "page_size": limit},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json().get("data", {})
        leads: list[Lead] = []
        for raw in data.get("list", []):
            field_data = {f.get("name", ""): f.get("value", "") for f in raw.get("field_data", [])}
            leads.append(
                Lead(
                    id=f"tiktok_{raw.get('lead_id', '')}",
                    platform="tiktok",
                    name=field_data.get("name", field_data.get("full_name", "")),
                    email=field_data.get("email", ""),
                    phone=field_data.get("phone_number", ""),
                    campaign=raw.get("campaign_name", "Campanha TikTok"),
                    created_at=datetime.fromisoformat(
                        raw.get("create_time", datetime.utcnow().isoformat())
                    ),
                    source_raw=raw,
                )
            )
        return leads

    def fetch_campaign_metrics(self) -> dict[str, Any]:
        advertiser_id = self.config["TIKTOK_ADVERTISER_ID"]
        response = requests.get(
            f"{TIKTOK_API_BASE}/report/integrated/get/",
            headers=self._headers(),
            params={
                "advertiser_id": advertiser_id,
                "report_type": "BASIC",
                "dimensions": '["advertiser_id"]',
                "metrics": '["impressions","clicks","spend"]',
                "data_level": "AUCTION_ADVERTISER",
            },
            timeout=15,
        )
        response.raise_for_status()
        rows = response.json().get("data", {}).get("list", [])
        row = (rows or [{}])[0].get("metrics", {})
        return {
            "impressions": int(row.get("impressions", 0)),
            "clicks": int(row.get("clicks", 0)),
            "spend": float(row.get("spend", 0.0)),
        }
