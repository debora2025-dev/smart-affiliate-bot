"""Agrega leads de todas as plataformas configuradas, com fallback para dados de demonstração.

Para cada plataforma em `integrations.REGISTRY`, tenta usar o conector real
(se as credenciais estiverem em `.env`); caso contrário, usa a fatia
correspondente dos dados de demonstração gerados por `core/demo_data.py`.
Isso garante que o dashboard sempre exiba números plausíveis, mesmo antes de
qualquer integração ser ativada, e migra silenciosamente para dados reais
assim que as credenciais forem preenchidas.
"""

from __future__ import annotations

import logging

from integrations import REGISTRY
from integrations.base import Lead

from . import demo_data

logger = logging.getLogger("marketing_pro")


class LeadManager:
    def __init__(self, config: dict[str, str]):
        self.config = config
        self._sources = {key: cls(config) for key, cls in REGISTRY.items()}
        self._demo_leads_cache: list[Lead] | None = None

    def _demo_leads(self) -> list[Lead]:
        if self._demo_leads_cache is None:
            self._demo_leads_cache = demo_data.generate_leads()
        return self._demo_leads_cache

    def platform_status(self) -> dict[str, dict]:
        """Indica, por plataforma, se está usando API real ou dados de demonstração."""
        status = {}
        for key, source in self._sources.items():
            configured = source.is_configured()
            status[key] = {
                "display_name": source.display_name,
                "connected": configured,
                "mode": "api_real" if configured else "demonstracao",
            }
        return status

    def get_all_leads(self) -> list[Lead]:
        leads: list[Lead] = []
        demo_leads_by_platform: dict[str, list[Lead]] = {}
        for lead in self._demo_leads():
            demo_leads_by_platform.setdefault(lead.platform, []).append(lead)

        for key, source in self._sources.items():
            if source.is_configured():
                try:
                    leads.extend(source.fetch_leads())
                    continue
                except Exception as exc:  # rede/credenciais inválidas: cai para demo
                    logger.warning("Falha ao buscar leads reais de %s: %s. Usando dados de demonstração.", key, exc)
            leads.extend(demo_leads_by_platform.get(key, []))

        leads.sort(key=lambda lead: lead.created_at, reverse=True)
        return leads

    def get_campaign_metrics(self) -> dict[str, dict]:
        metrics = {}
        for key, source in self._sources.items():
            if source.is_configured():
                try:
                    metrics[key] = source.fetch_campaign_metrics()
                    continue
                except Exception as exc:
                    logger.warning("Falha ao buscar métricas de campanha de %s: %s.", key, exc)
            metrics[key] = None  # sem dado de campanha real disponível em modo demo
        return metrics
