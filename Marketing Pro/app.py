"""Marketing Pro — Dashboard SaaS de leads qualificados (Meta, Google, LinkedIn, TikTok).

Como ativar:
    cd "Marketing Pro"
    pip install -r requirements.txt
    cp .env.example .env      # preencha as credenciais das plataformas que já tiver
    python app.py
    # abra http://localhost:5050

Sem nenhuma credencial preenchida, o dashboard já funciona com dados de
demonstração plausíveis (core/demo_data.py) para toda plataforma não
configurada — permitindo validar o layout e a lógica antes de ligar as APIs
reais. Assim que uma plataforma ganha credenciais válidas em `.env`, ela
passa a usar dados reais automaticamente, sem qualquer mudança de código.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from core import demo_data, metrics
from core.lead_manager import LeadManager

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("marketing_pro")

app = Flask(__name__)

CONFIG_KEYS = [
    "META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID", "META_PAGE_ID",
    "GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CUSTOMER_ID", "GOOGLE_ADS_ACCESS_TOKEN",
    "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AD_ACCOUNT_ID",
    "TIKTOK_ACCESS_TOKEN", "TIKTOK_ADVERTISER_ID",
]


def _config_from_env() -> dict[str, str]:
    return {key: os.getenv(key, "") for key in CONFIG_KEYS}


lead_manager = LeadManager(_config_from_env())


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/dashboard")
def api_dashboard():
    leads = lead_manager.get_all_leads()
    email_reviews = demo_data.generate_email_reviews(leads)
    calendar_events = demo_data.generate_calendar_events(leads)
    recovered_events = demo_data.generate_recovered_leads(leads)
    payload = metrics.build_dashboard_payload(
        leads=leads,
        email_reviews=email_reviews,
        calendar_events=calendar_events,
        recovered_events=recovered_events,
        platform_status=lead_manager.platform_status(),
    )
    return jsonify(payload)


@app.route("/api/status")
def api_status():
    return jsonify(lead_manager.platform_status())


if __name__ == "__main__":
    port = int(os.getenv("MARKETING_PRO_PORT", "5050"))
    logger.info("Marketing Pro rodando em http://localhost:%s", port)
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
