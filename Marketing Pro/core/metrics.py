"""Cálculo das métricas do dashboard a partir da lista normalizada de leads.

Cada função devolve um bloco de KPIs correspondente a um objetivo claro de
prospecção ativa, conforme solicitado:
  - funil de fechamento         -> funnel_metrics()
  - recuperação de leads        -> recovery_metrics()
  - revisão de e-mails          -> email_metrics()
  - vendas                      -> sales_metrics()
  - calendário                  -> calendar_metrics()
  - prospecção (por plataforma) -> prospecting_metrics()
"""

from __future__ import annotations

from datetime import datetime, timedelta

from integrations.base import Lead

FUNNEL_STAGES = ["novo", "qualificado", "contatado", "proposta", "fechado"]
PLATFORM_LABELS = {
    "meta": "Meta (Facebook/Instagram)",
    "google": "Google Ads",
    "linkedin": "LinkedIn",
    "tiktok": "TikTok",
}


def funnel_metrics(leads: list[Lead]) -> dict:
    """Funil de fechamento a partir de leads em snapshot (cada lead está em uma única etapa 'atual').

    Um lead na etapa "proposta" necessariamente já passou por "novo", "qualificado"
    e "contatado". Por isso a conversão é calculada sobre `reached_or_beyond`
    (quantos leads chegaram a essa etapa ou foram além dela), que é sempre
    monotonicamente decrescente — garantindo que nenhuma conversão passe de 100%,
    diferente de comparar as contagens brutas por etapa (que podem oscilar por
    serem independentes entre si).
    """
    counts = {stage: 0 for stage in FUNNEL_STAGES}
    for lead in leads:
        if lead.stage in counts:
            counts[lead.stage] += 1

    reached_or_beyond = []
    running = 0
    for stage in reversed(FUNNEL_STAGES):
        running += counts[stage]
        reached_or_beyond.append(running)
    reached_or_beyond.reverse()

    total_entradas = reached_or_beyond[0] if reached_or_beyond else 0
    stages_out = []
    previous_cumulative = None
    for stage, cumulative in zip(FUNNEL_STAGES, reached_or_beyond):
        conversion_from_previous = (
            round((cumulative / previous_cumulative) * 100, 1) if previous_cumulative else None
        )
        conversion_from_total = round((cumulative / total_entradas) * 100, 1) if total_entradas else 0.0
        stages_out.append(
            {
                "stage": stage,
                "label": stage.capitalize(),
                "quantity": counts[stage],
                "reached_or_beyond": cumulative,
                "conversion_from_previous_pct": conversion_from_previous,
                "conversion_from_total_pct": conversion_from_total,
            }
        )
        previous_cumulative = cumulative

    taxa_fechamento = round((reached_or_beyond[-1] / total_entradas) * 100, 1) if total_entradas else 0.0
    return {"stages": stages_out, "total_leads_no_funil": total_entradas, "taxa_fechamento_pct": taxa_fechamento}


def recovery_metrics(leads: list[Lead], recovered_events: list[dict]) -> dict:
    perdidos = [lead for lead in leads if lead.stage == "perdido"]
    total_perdidos = len(perdidos)
    total_recuperados = len(recovered_events)
    taxa_recuperacao = round((total_recuperados / total_perdidos) * 100, 1) if total_perdidos else 0.0
    valor_recuperado_estimado = round(total_recuperados * 2400.0, 2)
    por_canal: dict[str, int] = {}
    for event in recovered_events:
        canal = event["recovery_channel"]
        por_canal[canal] = por_canal.get(canal, 0) + 1
    return {
        "leads_perdidos": total_perdidos,
        "leads_recuperados": total_recuperados,
        "taxa_recuperacao_pct": taxa_recuperacao,
        "valor_recuperado_estimado": valor_recuperado_estimado,
        "recuperacoes_por_canal": por_canal,
        "eventos_recentes": recovered_events[:8],
    }


def email_metrics(email_reviews: list[dict]) -> dict:
    total = len(email_reviews)
    por_status: dict[str, int] = {}
    for item in email_reviews:
        por_status[item["status"]] = por_status.get(item["status"], 0) + 1

    enviados = [item for item in email_reviews if item["open_rate"] is not None]
    respondidos = [item for item in email_reviews if item["reply_rate"] is not None]
    taxa_abertura_media = round(sum(item["open_rate"] for item in enviados) / len(enviados) * 100, 1) if enviados else 0.0
    taxa_resposta_media = (
        round(sum(item["reply_rate"] for item in respondidos) / len(respondidos) * 100, 1) if respondidos else 0.0
    )
    pendentes_revisao = por_status.get("em_revisao", 0) + por_status.get("rascunho", 0)
    return {
        "total_emails": total,
        "pendentes_de_revisao": pendentes_revisao,
        "por_status": por_status,
        "taxa_abertura_media_pct": taxa_abertura_media,
        "taxa_resposta_media_pct": taxa_resposta_media,
        "fila_revisao": [item for item in email_reviews if item["status"] in ("rascunho", "em_revisao")][:8],
    }


def sales_metrics(leads: list[Lead]) -> dict:
    fechados = [lead for lead in leads if lead.stage == "fechado"]
    receita_total = round(sum(lead.estimated_value for lead in fechados), 2)
    ticket_medio = round(receita_total / len(fechados), 2) if fechados else 0.0

    por_plataforma: dict[str, dict] = {}
    for lead in fechados:
        bucket = por_plataforma.setdefault(lead.platform, {"quantidade": 0, "receita": 0.0})
        bucket["quantidade"] += 1
        bucket["receita"] += lead.estimated_value
    for bucket in por_plataforma.values():
        bucket["receita"] = round(bucket["receita"], 2)

    em_proposta = [lead for lead in leads if lead.stage == "proposta"]
    pipeline_em_aberto = round(sum(lead.estimated_value for lead in em_proposta), 2)

    return {
        "vendas_fechadas": len(fechados),
        "receita_total": receita_total,
        "ticket_medio": ticket_medio,
        "pipeline_em_proposta": pipeline_em_aberto,
        "por_plataforma": por_plataforma,
        "negocios_recentes": sorted(
            [
                {
                    "lead_id": lead.id,
                    "lead_name": lead.name,
                    "platform": lead.platform,
                    "valor": lead.estimated_value,
                    "fechado_em": lead.created_at.isoformat(),
                }
                for lead in fechados
            ],
            key=lambda item: item["fechado_em"],
            reverse=True,
        )[:8],
    }


def calendar_metrics(events: list[dict]) -> dict:
    now = datetime.utcnow()
    proximos_7_dias = [e for e in events if now <= datetime.fromisoformat(e["starts_at"]) <= now + timedelta(days=7)]
    por_tipo: dict[str, int] = {}
    for event in proximos_7_dias:
        por_tipo[event["type"]] = por_tipo.get(event["type"], 0) + 1
    return {
        "compromissos_proximos_7_dias": len(proximos_7_dias),
        "por_tipo": por_tipo,
        "proxima_agenda": proximos_7_dias[:10],
    }


def prospecting_metrics(leads: list[Lead]) -> dict:
    ativos = [lead for lead in leads if lead.stage in ("qualificado", "contatado", "proposta")]
    contatados = [lead for lead in leads if lead.stage in ("contatado", "proposta", "fechado")]
    total = len(leads)
    taxa_qualificacao = (
        round(len([lead for lead in leads if lead.stage != "novo"]) / total * 100, 1) if total else 0.0
    )
    taxa_contato = round(len(contatados) / total * 100, 1) if total else 0.0

    por_plataforma = []
    for key, label in PLATFORM_LABELS.items():
        platform_leads = [lead for lead in leads if lead.platform == key]
        score_medio = round(sum(lead.score for lead in platform_leads) / len(platform_leads), 1) if platform_leads else 0.0
        por_plataforma.append(
            {
                "platform": key,
                "label": label,
                "total_leads": len(platform_leads),
                "leads_ativos_em_prospeccao": len([lead for lead in platform_leads if lead in ativos]),
                "score_medio_qualificacao": score_medio,
            }
        )

    return {
        "total_leads_recebidos": total,
        "leads_em_prospeccao_ativa": len(ativos),
        "taxa_qualificacao_pct": taxa_qualificacao,
        "taxa_contato_pct": taxa_contato,
        "por_plataforma": por_plataforma,
    }


def build_dashboard_payload(
    leads: list[Lead],
    email_reviews: list[dict],
    calendar_events: list[dict],
    recovered_events: list[dict],
    platform_status: dict,
) -> dict:
    """Monta o payload único consumido pelo frontend (`/api/dashboard`)."""
    return {
        "gerado_em": datetime.utcnow().isoformat(),
        "status_plataformas": platform_status,
        "funil_fechamento": funnel_metrics(leads),
        "recuperacao_leads": recovery_metrics(leads, recovered_events),
        "revisao_emails": email_metrics(email_reviews),
        "vendas": sales_metrics(leads),
        "calendario": calendar_metrics(calendar_events),
        "prospeccao": prospecting_metrics(leads),
        "leads_recentes": [lead.to_dict() for lead in leads[:25]],
    }
