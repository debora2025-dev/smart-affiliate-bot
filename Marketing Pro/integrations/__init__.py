"""Conectores de plataformas de anúncios/leads (Meta, Google, LinkedIn, TikTok)."""

from .base import Lead, LeadSource
from .meta_ads import MetaAdsSource
from .google_ads import GoogleAdsSource
from .linkedin_ads import LinkedInAdsSource
from .tiktok_ads import TikTokAdsSource

REGISTRY = {
    "meta": MetaAdsSource,
    "google": GoogleAdsSource,
    "linkedin": LinkedInAdsSource,
    "tiktok": TikTokAdsSource,
}

__all__ = ["Lead", "LeadSource", "REGISTRY"]
