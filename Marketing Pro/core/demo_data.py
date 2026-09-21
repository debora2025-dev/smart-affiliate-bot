"""Gerador de dados de demonstração plausíveis.

Quando uma plataforma (Meta, Google, LinkedIn, TikTok) não tem credenciais
configuradas em `.env`, o dashboard usa estes geradores para exibir números
realistas de leads, funil, e-mails, vendas e agenda — permitindo validar o
layout e a lógica de métricas antes de ligar as APIs reais. Basta preencher
o `.env` (ver `.env.example`) para cada plataforma passar a usar dados reais.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from integrations.base import Lead

_FIRST_NAMES = [
    "Ana", "Bruno", "Carla", "Diego", "Elisa", "Fábio", "Gabriela", "Henrique",
    "Isabela", "João", "Karina", "Lucas", "Mariana", "Nicolas", "Olívia",
    "Paulo", "Renata", "Sérgio", "Tatiana", "Vinícius",
]
_LAST_NAMES = [
    "Silva", "Souza", "Oliveira", "Santos", "Pereira", "Costa", "Almeida",
    "Ferreira", "Rodrigues", "Carvalho",
]

_CAMPAIGNS = {
    "meta": ["Leads Quentes - Black Friday", "Remarketing Carrinho", "Captação Instagram Reels"],
    "google": ["Pesquisa - Palavras-chave de Marca", "Display Remarketing", "Performance Max"],
    "linkedin": ["Decisores B2B - Diretoria", "Lead Gen Form - Webinar", "InMail Prospecção"],
    "tiktok": ["Spark Ads - Geração Z", "Lead Gen TopView", "Criativos UGC"],
}

_STAGE_WEIGHTS = [
    ("novo", 0.30),
    ("qualificado", 0.24),
    ("contatado", 0.20),
    ("proposta", 0.14),
    ("fechado", 0.07),
    ("perdido", 0.05),
]

_EMAIL_STATUSES = ["rascunho", "em_revisao", "aprovado", "enviado", "respondido"]


def _weighted_stage(rng: random.Random) -> str:
    stages, weights = zip(*_STAGE_WEIGHTS)
    return rng.choices(stages, weights=weights, k=1)[0]


def generate_leads(seed: int = 42, per_platform: int = 18) -> list[Lead]:
    """Gera leads plausíveis para as 4 plataformas com distribuição realista de funil."""
    rng = random.Random(seed)
    now = datetime.utcnow()
    leads: list[Lead] = []
    counter = 0
    for platform, campaigns in _CAMPAIGNS.items():
        for _ in range(per_platform):
            counter += 1
            name = f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}"
            stage = _weighted_stage(rng)
            score = {
                "novo": rng.randint(30, 55),
                "qualificado": rng.randint(55, 75),
                "contatado": rng.randint(60, 80),
                "proposta": rng.randint(75, 92),
                "fechado": rng.randint(85, 100),
                "perdido": rng.randint(10, 40),
            }[stage]
            created_at = now - timedelta(
                days=rng.randint(0, 29), hours=rng.randint(0, 23), minutes=rng.randint(0, 59)
            )
            estimated_value = round(rng.uniform(800, 12000), 2) if stage != "perdido" else 0.0
            slug = name.lower().replace(" ", ".")
            leads.append(
                Lead(
                    id=f"{platform}_{counter:04d}",
                    platform=platform,
                    name=name,
                    email=f"{slug}@exemplo.com",
                    phone=f"+55 {rng.randint(11, 99)} 9{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}",
                    campaign=rng.choice(campaigns),
                    created_at=created_at,
                    stage=stage,
                    score=score,
                    estimated_value=estimated_value,
                )
            )
    leads.sort(key=lambda lead: lead.created_at, reverse=True)
    return leads


def generate_email_reviews(leads: list[Lead], seed: int = 7) -> list[dict]:
    """Gera itens de revisão de e-mail (sequências de nutrição/follow-up) por lead."""
    rng = random.Random(seed)
    subjects = [
        "Vamos falar sobre o seu objetivo com [Empresa]?",
        "Proposta personalizada disponível",
        "3 formas de resolver {problema} rapidamente",
        "Última chamada: condição especial expira hoje",
        "Follow-up: alguma dúvida sobre a proposta?",
    ]
    reviews = []
    for lead in leads:
        if lead.stage in ("novo", "qualificado", "contatado", "proposta"):
            status = rng.choice(_EMAIL_STATUSES)
            reviews.append(
                {
                    "lead_id": lead.id,
                    "lead_name": lead.name,
                    "platform": lead.platform,
                    "subject": rng.choice(subjects),
                    "status": status,
                    "open_rate": round(rng.uniform(0.18, 0.62), 2) if status in ("enviado", "respondido") else None,
                    "reply_rate": round(rng.uniform(0.02, 0.22), 2) if status == "respondido" else None,
                    "scheduled_at": (lead.created_at + timedelta(days=rng.randint(1, 5))).isoformat(),
                }
            )
    return reviews


def generate_calendar_events(leads: list[Lead], seed: int = 11) -> list[dict]:
    """Gera compromissos de agenda (calls de prospecção, demos, follow-ups) nos próximos dias."""
    rng = random.Random(seed)
    event_types = [
        "Chamada de descoberta",
        "Demonstração do produto",
        "Follow-up comercial",
        "Reunião de fechamento",
    ]
    now = datetime.utcnow()
    candidates = [lead for lead in leads if lead.stage in ("qualificado", "contatado", "proposta")]
    events = []
    for lead in rng.sample(candidates, k=min(14, len(candidates))):
        start = now + timedelta(days=rng.randint(0, 6), hours=rng.randint(8, 17))
        events.append(
            {
                "lead_id": lead.id,
                "lead_name": lead.name,
                "platform": lead.platform,
                "type": rng.choice(event_types),
                "starts_at": start.isoformat(),
                "duration_minutes": rng.choice([15, 30, 45, 60]),
            }
        )
    events.sort(key=lambda event: event["starts_at"])
    return events


def generate_recovered_leads(leads: list[Lead], seed: int = 5) -> list[dict]:
    """Gera leads 'perdidos' que foram reabordados e recuperados para o funil (recuperação de leads)."""
    rng = random.Random(seed)
    lost = [lead for lead in leads if lead.stage == "perdido"]
    recovered = rng.sample(lost, k=min(6, len(lost)))
    return [
        {
            "lead_id": lead.id,
            "lead_name": lead.name,
            "platform": lead.platform,
            "recovered_at": (lead.created_at + timedelta(days=rng.randint(3, 20))).isoformat(),
            "recovery_channel": rng.choice(["E-mail de reativação", "Retargeting pago", "Ligação ativa", "WhatsApp"]),
        }
        for lead in recovered
    ]
