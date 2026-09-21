"""Contrato comum que todo conector de plataforma (Meta, Google, LinkedIn, TikTok) implementa.

Cada conector normaliza os dados da API nativa da plataforma para o schema
`Lead` único, permitindo que o restante do dashboard (core/lead_manager.py,
core/metrics.py) trate todas as origens da mesma forma.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Lead:
    """Representação normalizada de um lead, independente da plataforma de origem."""

    id: str
    platform: str  # meta | google | linkedin | tiktok
    name: str
    email: str
    phone: str
    campaign: str
    created_at: datetime
    stage: str = "novo"  # novo -> qualificado -> contatado -> proposta -> fechado | perdido
    score: int = 0  # 0-100, qualificação do lead
    estimated_value: float = 0.0
    source_raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "platform": self.platform,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "campaign": self.campaign,
            "created_at": self.created_at.isoformat(),
            "stage": self.stage,
            "score": self.score,
            "estimated_value": self.estimated_value,
        }


class LeadSource:
    """Classe base para um conector de plataforma.

    Subclasses implementam `fetch_leads()` e `fetch_campaign_metrics()` usando a
    API oficial da plataforma. Quando as credenciais não estão configuradas em
    `.env`, `is_configured()` retorna False e o dashboard usa dados de
    demonstração (core/demo_data.py) para aquela plataforma, mantendo o app
    funcional out-of-the-box.
    """

    platform_key: str = "base"
    display_name: str = "Base"

    def __init__(self, config: dict[str, str]):
        self.config = config

    def is_configured(self) -> bool:
        raise NotImplementedError

    def fetch_leads(self, limit: int = 50) -> list[Lead]:
        raise NotImplementedError

    def fetch_campaign_metrics(self) -> dict[str, Any]:
        """Retorna métricas agregadas de campanha: impressões, cliques, custo, CPL."""
        raise NotImplementedError
