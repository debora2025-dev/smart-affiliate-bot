# Smart Affiliate Bot | Monitoramento & Automação RPA

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=for-the-badge&logo=pandas&logoColor=white)
![CI](https://github.com/debora2025-dev/smart-affiliate-bot/actions/workflows/ci.yml/badge.svg)
![Status](https://img.shields.io/badge/Status-Em%20Produção-success?style=for-the-badge)

Ecossistema completo de **RPA (Robotic Process Automation)** para automação de curadoria, validação e postagem de ofertas em grupos de afiliados (WhatsApp e Telegram). Une Web Scraping com análise histórica de preços via Pandas para garantir que apenas promoções genuínas sejam enviadas.

---

## A Persona: "Celle"

O projeto utiliza a **Celle**, um avatar 3D que humaniza a curadoria e gera autoridade no nicho. A Celle representa a "inteligência" por trás da seleção de produtos, aumentando o engajamento no grupo **Achadinhos da Celle**.

---

## Funcionalidades

| Módulo | Descrição |
|---|---|
| `rastreador_ofertas.py` | Core do bot — scraping, validação, envio WhatsApp/Telegram |
| `utils/validador_preco.py` | Análise histórica de preços com Pandas (detecta descontos genuínos) |
| `utils/logger.py` | Logging centralizado com rotação diária (`logs/bot_YYYY-MM-DD.log`) |
| `utils/agendador.py` | Agendador de turnos diários (Manhã, Almoço, Tarde, Noite, Cupons) |
| `TELEGRAM-WPP/telegram_bot.py` | Bridge Telegram → WhatsApp |
| `utils/rastreador_manual.py` | Envio manual via arquivo de links |
| `utils/rastreador_ml.py` | Scraper dedicado Mercado Livre |

**Fontes monitoradas:** Amazon · Mercado Livre · Magazine Luiza · Shopee

**Recursos:**
- Detecção de desconto genuíno vs. aumento de preço com histórico CSV
- Cache de 24h anti-spam/anti-duplicata
- Mimetismo humano via depuração remota Chrome (porta 9222)
- Copywriting dinâmico por nicho (Beleza, Tecnologia, Casa)
- Agendamento automático por turnos estratégicos

---

## Estrutura do Projeto

```
smart-affiliate-bot/
│
├── rastreador_ofertas.py          # Core do Bot (RPA principal)
├── requirements.txt               # Dependências Python
├── setup.bat                      # Setup automático (Windows)
├── .env.example                   # Template de variáveis de ambiente
├── .gitignore
│
├── .github/workflows/
│   └── ci.yml                     # GitHub Actions – testes automáticos
│
├── utils/
│   ├── validador_preco.py         # Análise histórica de preços (Pandas)
│   ├── logger.py                  # Sistema de logging centralizado
│   ├── agendador.py               # Agendador de turnos diários
│   ├── rastreador_manual.py       # Envio manual por lista de links
│   ├── rastreador_ml.py           # Scraper Mercado Livre
│   └── promoclick_bridge.js       # Sender Telegram/Promoção
│
├── TELEGRAM-WPP/
│   └── telegram_bot.py            # Bridge Telegram → WhatsApp
│
├── testes_homologacao/
│   ├── teste_validador.py         # Testes unitários do validador
│   ├── teste_integracao.py        # Teste de integração completo
│   └── teste_whatsapp.py          # Teste de envio WhatsApp
│
├── scripts_automacao/             # Scripts .bat por turno/plataforma
├── docs/                          # Estratégias de vendas e postagens
└── assets/                        # Imagens e recursos visuais
```

---

## Instalação

### Opção A — Setup automático (recomendado)

```bat
git clone https://github.com/debora2025-dev/smart-affiliate-bot.git
cd smart-affiliate-bot
setup.bat
```

O `setup.bat` cria o `.venv`, instala dependências, gera o `.env` e roda os testes.

### Opção B — Manual

```bash
# 1. Clonar e acessar o diretório
git clone https://github.com/debora2025-dev/smart-affiliate-bot.git
cd smart-affiliate-bot

# 2. Criar e ativar ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
copy .env.example .env
# Edite o .env com seus tokens

# 5. Rodar testes
python -m pytest testes_homologacao/ -v
```

---

## Configuração do `.env`

```env
TELEGRAM_BOT_TOKEN=seu_token_do_bot
TELEGRAM_CHAT_ID=seu_chat_id
GRUPO_WHATSAPP=Achadinhos da Celle • AI
CHROME_DEBUG_PORT=9222
AMAZON_TAG=seu-tag-20
MAGALU_BASE_URL=https://www.magazinevoce.com.br/magazinesualoja/
SIMULAR_DIGITACAO=True
DELAY_MIN=5
DELAY_MAX=15
```

Todos os campos disponíveis estão documentados em `.env.example`.

---

## Executar

```bat
:: Iniciar Chrome no modo debug (necessário para WhatsApp Web)
chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\ChromeBot

:: Executar o bot principal
python rastreador_ofertas.py

:: Executar com agendamento automático de turnos
python utils\agendador.py

:: Ver turnos configurados
python utils\agendador.py --listar

:: Envio manual de lista de links
python utils\rastreador_manual.py
```

**Turnos automáticos (configuráveis em `utils/agendador.py`):**

| Turno | Horário |
|---|---|
| Manhã | 09:00 |
| Almoço | 12:30 |
| Tarde | 15:30 |
| Noite | 20:00 |
| Cupons | 09:15 |
| Feminino | 10:00 |

---

## Testes

```bash
# Todos os testes
python -m pytest testes_homologacao/ -v

# Apenas unitários (sem dependências externas)
python -m pytest testes_homologacao/teste_validador.py -v

# Integração completa
python -m pytest testes_homologacao/teste_integracao.py -v
```

Os testes de homologação são executados automaticamente via **GitHub Actions** a cada push na branch `main`.

---

## Tecnologias

| Tecnologia | Uso |
|---|---|
| Python 3.13 | Linguagem principal |
| Selenium 4.x | Automação do WhatsApp Web |
| BeautifulSoup4 | Web scraping de ofertas |
| Pandas 2.x | Análise histórica de preços |
| python-dotenv | Gestão de segredos |
| schedule | Agendamento de turnos |
| pywin32 / pyperclip | Clipboard Windows |
| Pillow | Manipulação de imagens |

---

## Segurança

- Credenciais gerenciadas via `.env` (nunca commitadas)
- `.gitignore` configurado para excluir `.env`, `.venv`, `logs/` e caches
- Chrome via depuração remota (porta 9222) evita detecção por anti-bot
- Sistema de cache 24h previne spam

---

<p align="center">
  Desenvolvido com Python por <strong>Marcelle Santos</strong><br>
  Analista de Service Desk & Desenvolvedora Python · Nova Iguaçu, RJ
</p>
