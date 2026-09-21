"""Conector LinkedIn — Lead Gen Forms via LinkedIn Marketing API (REST).

Requer um app aprovado no LinkedIn Developer Portal com o produto
"Marketing Developer Platform" e um access token OAuth2 com escopo
`r_ads_leadgen_automation` e `r_ads_reporting`.
Ver: https://learn.microsoft.com/linkedin/marketing/integrations/lead-gen/lead-gen-forms

Variáveis de ambiente:
    LINKEDIN_ACCESS_TOKEN
    LINKEDIN_AD_ACCOUNT_ID   - ex: "urn:li:sponsoredAccount:123456789"
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from .base import Lead, LeadSource

LINKEDIN_API_BASE = "https://api.linkedin.com/rest"
LINKEDIN_API_VERSION = "202409"


class LinkedInAdsSource(LeadSource):
    platform_key = "linkedin"
    display_name = "LinkedIn Ads"

    def is_configured(self) -> bool:
        return bool(self.config.get("LINKEDIN_ACCESS_TOKEN") and self.config.get("LINKEDIN_AD_ACCOUNT_ID"))

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config['LINKEDIN_ACCESS_TOKEN']}",
            "LinkedIn-Version": LINKEDIN_API_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def fetch_leads(self, limit: int = 50) -> list[Lead]:
        account = self.config["LINKEDIN_AD_ACCOUNT_ID"]
        response = requests.get(
            f"{LINKEDIN_API_BASE}/leadFormResponses",
            headers=self._headers(),
            params={"q": "sponsoredAccount", "sponsoredAccount": account, "count": limit},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        leads: list[Lead] = []
        for raw in data.get("elements", []):
            answers = {a.get("questionId", ""): a.get("answer", "") for a in raw.get("formResponse", [])}
            leads.append(
                Lead(
                    id=f"linkedin_{raw.get('id', '')}",
                    platform="linkedin",
                    name=answers.get("FIRST_NAME", "") + " " + answers.get("LAST_NAME", ""),
                    email=answers.get("EMAIL", ""),
                    phone=answers.get("PHONE_NUMBER", ""),
                    campaign=raw.get("campaignName", "Campanha LinkedIn"),
                    created_at=datetime.fromtimestamp(raw.get("submittedAt", 0) / 1000),
                    source_raw=raw,
                )
            )
        return leads

    def fetch_campaign_metrics(self) -> dict[str, Any]:
        account = self.config["LINKEDIN_AD_ACCOUNT_ID"]
        response = requests.get(
            f"{LINKEDIN_API_BASE}/adAnalytics",
            headers=self._headers(),
            params={
                "q": "analytics",
                "pivot": "CAMPAIGN",
                "dateRange.start.day": 1,
                "accounts[0]": account,
                "fields": "impressions,clicks,costInLocalCurrency",
            },
            timeout=15,
        )
        response.raise_for_status()
        rows = response.json().get("elements", [])
        impressions = sum(int(r.get("impressions", 0)) for r in rows)
        clicks = sum(int(r.get("clicks", 0)) for r in rows)
        spend = sum(float(r.get("costInLocalCurrency", 0.0)) for r in rows)
        return {"impressions": impressions, "clicks": clicks, "spend": spend}
