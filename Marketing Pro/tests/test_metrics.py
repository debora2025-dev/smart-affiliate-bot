import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import demo_data, metrics


def _sample_leads():
    return demo_data.generate_leads(seed=1, per_platform=10)


def test_generate_leads_covers_all_platforms():
    leads = _sample_leads()
    platforms = {lead.platform for lead in leads}
    assert platforms == {"meta", "google", "linkedin", "tiktok"}
    assert len(leads) == 40


def test_funnel_metrics_conservation():
    leads = _sample_leads()
    result = metrics.funnel_metrics(leads)
    stage_total = sum(stage["quantity"] for stage in result["stages"])
    assert stage_total == result["total_leads_no_funil"]
    assert 0 <= result["taxa_fechamento_pct"] <= 100


def test_funnel_metrics_is_monotonic_and_bounded():
    leads = _sample_leads()
    result = metrics.funnel_metrics(leads)
    cumulative = [stage["reached_or_beyond"] for stage in result["stages"]]
    assert cumulative == sorted(cumulative, reverse=True)
    for stage in result["stages"]:
        if stage["conversion_from_previous_pct"] is not None:
            assert 0 <= stage["conversion_from_previous_pct"] <= 100


def test_recovery_metrics_rate_bounds():
    leads = _sample_leads()
    recovered = demo_data.generate_recovered_leads(leads, seed=1)
    result = metrics.recovery_metrics(leads, recovered)
    assert result["leads_recuperados"] == len(recovered)
    assert 0 <= result["taxa_recuperacao_pct"] <= 100


def test_email_metrics_pending_never_negative():
    leads = _sample_leads()
    reviews = demo_data.generate_email_reviews(leads, seed=1)
    result = metrics.email_metrics(reviews)
    assert result["pendentes_de_revisao"] >= 0
    assert result["total_emails"] == len(reviews)


def test_sales_metrics_revenue_matches_closed_leads():
    leads = _sample_leads()
    result = metrics.sales_metrics(leads)
    closed = [lead for lead in leads if lead.stage == "fechado"]
    assert result["vendas_fechadas"] == len(closed)
    assert result["receita_total"] == round(sum(lead.estimated_value for lead in closed), 2)


def test_calendar_metrics_window_is_seven_days():
    leads = _sample_leads()
    events = demo_data.generate_calendar_events(leads, seed=1)
    result = metrics.calendar_metrics(events)
    assert len(result["proxima_agenda"]) == min(result["compromissos_proximos_7_dias"], 10)


def test_prospecting_metrics_percentages_bounded():
    leads = _sample_leads()
    result = metrics.prospecting_metrics(leads)
    assert 0 <= result["taxa_qualificacao_pct"] <= 100
    assert 0 <= result["taxa_contato_pct"] <= 100
    assert len(result["por_plataforma"]) == 4


def test_build_dashboard_payload_has_all_sections():
    leads = _sample_leads()
    payload = metrics.build_dashboard_payload(
        leads=leads,
        email_reviews=demo_data.generate_email_reviews(leads, seed=1),
        calendar_events=demo_data.generate_calendar_events(leads, seed=1),
        recovered_events=demo_data.generate_recovered_leads(leads, seed=1),
        platform_status={"meta": {"connected": False}},
    )
    expected_keys = {
        "gerado_em", "status_plataformas", "funil_fechamento", "recuperacao_leads",
        "revisao_emails", "vendas", "calendario", "prospeccao", "leads_recentes",
    }
    assert expected_keys.issubset(payload.keys())
