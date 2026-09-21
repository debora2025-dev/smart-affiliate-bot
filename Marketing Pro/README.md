# Marketing Pro

Dashboard SaaS de **leads qualificados a receber** — construído para prospecção
ativa e abordagem comercial, com integração a **Meta (Facebook/Instagram)**,
**Google Ads**, **LinkedIn Ads** e **TikTok Ads**.

Objetivos que o dashboard deixa claros em uma única tela:

| Bloco | O que mostra |
|---|---|
| **Funil de fechamento** | Quantos leads chegam a cada etapa (novo → qualificado → contatado → proposta → fechado) e a taxa de conversão real entre etapas |
| **Recuperação de leads** | Quantos leads perdidos foram reabordados com sucesso e por qual canal |
| **Revisão de e-mails** | Fila de e-mails pendentes de aprovação, taxa de abertura e de resposta |
| **Vendas** | Receita fechada, ticket médio, pipeline em proposta, negócios recentes |
| **Calendário** | Reuniões de prospecção/fechamento agendadas para os próximos 7 dias |
| **Prospecção** | Volume de leads e score médio de qualificação por plataforma |

## Como ativar

```bash
cd "Marketing Pro"
pip install -r requirements.txt
cp .env.example .env      # opcional: preencha credenciais das plataformas que já tiver
python app.py
```

Abra `http://localhost:5050`.

Sem nenhuma credencial preenchida no `.env`, o dashboard já funciona com
**dados de demonstração plausíveis** (gerados por `core/demo_data.py`) para
toda plataforma não configurada — dá para validar layout, métricas e fluxo
sem esperar aprovação de nenhuma API. A barra superior do dashboard mostra,
por plataforma, se está em modo "API real" ou "demonstração".

## Ativando as integrações reais

Cada plataforma tem um conector dedicado em `integrations/`, que troca
automaticamente de demonstração para dados reais assim que as variáveis
correspondentes existirem no `.env` (ver `.env.example` para a lista
completa e onde gerar cada credencial):

| Plataforma | Arquivo | Credenciais necessárias |
|---|---|---|
| Meta (Facebook/Instagram) | `integrations/meta_ads.py` | `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` |
| Google Ads | `integrations/google_ads.py` | `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID`, `GOOGLE_ADS_ACCESS_TOKEN` |
| LinkedIn Ads | `integrations/linkedin_ads.py` | `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_AD_ACCOUNT_ID` |
| TikTok Ads | `integrations/tiktok_ads.py` | `TIKTOK_ACCESS_TOKEN`, `TIKTOK_ADVERTISER_ID` |

Se uma credencial estiver inválida ou a API falhar, o `LeadManager`
(`core/lead_manager.py`) registra um aviso no log e recai para os dados de
demonstração daquela plataforma — o dashboard nunca quebra por falta ou
expiração de token.

## Estrutura

```
Marketing Pro/
├── app.py                     # servidor Flask (rotas / e /api/dashboard)
├── integrations/               # 1 conector por plataforma + contrato comum (base.py)
│   ├── base.py
│   ├── meta_ads.py
│   ├── google_ads.py
│   ├── linkedin_ads.py
│   └── tiktok_ads.py
├── core/
│   ├── demo_data.py            # dados de demonstração plausíveis
│   ├── lead_manager.py         # agrega leads reais + fallback demo por plataforma
│   └── metrics.py              # cálculo de todos os KPIs do dashboard
├── templates/dashboard.html
├── static/css/dashboard.css
├── static/js/dashboard.js      # consome /api/dashboard e desenha os gráficos
└── tests/test_metrics.py       # testes das regras de negócio das métricas
```

## Testes

```bash
cd "Marketing Pro"
python -m pytest tests/ -v
```
