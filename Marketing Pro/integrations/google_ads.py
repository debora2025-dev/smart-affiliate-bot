"""Conector Google Ads — Lead Form Extensions e métricas via Google Ads API (REST).

Requer uma conta de desenvolvedor aprovada no Google Ads API Center e um
OAuth2 refresh token com escopo `https://www.googleapis.com/auth/adwords`.
Ver: https://developers.google.com/google-ads/api/docs/first-call/overview

Variáveis de ambiente:
    GOOGLE_ADS_DEVELOPER_TOKEN
    GOOGLE_ADS_CUSTOMER_ID     - sem hífens, ex: "1234567890"
    GOOGLE_ADS_ACCESS_TOKEN    - access token OAuth2 válido (renovado externamente)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from .base import Lead, LeadSource

GOOGLE_ADS_API_VERSION = "v18"
GOOGLE_ADS_API_BASE = f"https://googleads.googleapis.com/{GOOGLE_ADS_API_VERSION}"


class GoogleAdsSource(LeadSource):
    platform_key = "google"
    display_name = "Google Ads"

    def is_configured(self) -> bool:
        return bool(
            self.config.get("GOOGLE_ADS_DEVELOPER_TOKEN")
            and self.config.get("GOOGLE_ADS_CUSTOMER_ID")
            and self.config.get("GOOGLE_ADS_ACCESS_TOKEN")
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config['GOOGLE_ADS_ACCESS_TOKEN']}",
            "developer-token": self.config["GOOGLE_ADS_DEVELOPER_TOKEN"],
            "Content-Type": "application/json",
        }

    def _search_stream(self, query: str) -> list[dict[str, Any]]:
        customer_id = self.config["GOOGLE_ADS_CUSTOMER_ID"]
        url = f"{GOOGLE_ADS_API_BASE}/customers/{customer_id}/googleAds:searchStream"
        response = requests.post(url, headers=self._headers(), json={"query": query}, timeout=15)
        response.raise_for_status()
        rows: list[dict[str, Any]] = []
        for batch in response.json():
            rows.extend(batch.get("results", []))
        return rows

    def fetch_leads(self, limit: int = 50) -> list[Lead]:
        query = f"""
            SELECT lead_form_submission_data.resource_name,
                   lead_form_submission_data.submission_date_time,
                   lead_form_submission_data.campaign,
                   lead_form_submission_data.lead_form_submission_fields
            FROM lead_form_submission_data
            ORDER BY lead_form_submission_data.submission_date_time DESC
            LIMIT {limit}
        """
        rows = self._search_stream(query)
        leads: list[Lead] = []
        for row in rows:
            submission = row.get("leadFormSubmissionData", {})
            fields = {
                f.get("fieldType", ""): f.get("fieldValue", "")
                for f in submission.get("leadFormSubmissionFields", [])
            }
            leads.append(
                Lead(
                    id=f"google_{submission.get('resourceName', '')}",
                    platform="google",
                    name=fields.get("FULL_NAME", fields.get("FIRST_NAME", "")),
                    email=fields.get("EMAIL", ""),
                    phone=fields.get("PHONE_NUMBER", ""),
                    campaign=submission.get("campaign", "Campanha Google Ads"),
                    created_at=datetime.fromisoformat(
                        submission.get("submissionDateTime", datetime.utcnow().isoformat())
                    ),
                    source_raw=submission,
                )
            )
        return leads

    def fetch_campaign_metrics(self) -> dict[str, Any]:
        query = """
            SELECT metrics.impressions, metrics.clicks, metrics.cost_micros
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
        """
        rows = self._search_stream(query)
        impressions = sum(int(r.get("metrics", {}).get("impressions", 0)) for r in rows)
        clicks = sum(int(r.get("metrics", {}).get("clicks", 0)) for r in rows)
        spend = sum(int(r.get("metrics", {}).get("costMicros", 0)) for r in rows) / 1_000_000
        return {"impressions": impressions, "clicks": clicks, "spend": spend}
