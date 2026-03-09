# Changelog

Todas as mudanças notáveis neste projeto estão documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [Unreleased]

---

## [1.1.0] – 2026-03-09

### Adicionado
- `utils/validador_preco.py` – análise histórica de preços com Pandas; detecta se um desconto é genuíno comparando com mínimos e médias históricas
- `utils/logger.py` – sistema de logging centralizado com rotação diária, substitui `print()` dispersos pelo código
- `utils/agendador.py` – agendador de turnos diários (Manhã, Almoço, Tarde, Noite, Cupons, Feminino) usando a biblioteca `schedule`; substitui os scripts `.bat` de agendamento manual
- `.env.example` – template completo de variáveis de ambiente com todos os parâmetros do bot documentados
- `links.txt.example` – template de formato para o modo de envio manual de links
- `shopee_links.txt.example` – template para envio manual de links Shopee
- `testes_homologacao/teste_validador.py` – 5 testes unitários para `validador_preco.py`
- `testes_homologacao/teste_integracao.py` – teste de integração completo: importações, dependências, arquivos essenciais, lógica do validador e logger
- `setup.bat` – script de setup automático Windows: cria `.venv`, instala dependências, gera `.env` e roda testes
- `.github/workflows/ci.yml` – GitHub Actions CI: roda testes automaticamente a cada push em `main` e `develop`
- `CHANGELOG.md` – este arquivo

### Corrigido
- `rastreador_ofertas.py`: `ARQUIVO_CACHE_ENVIOS` era usado antes de ser definido (linha ~133 vs. definição na linha ~2796) — movido para o início do arquivo
- `rastreador_ofertas.py`: função `atualizar_historico(arquivo_csv, titulo, preco_coletado)` usava variável `preco` indefinida; corrigido para usar o parâmetro `preco_coletado`
- `rastreador_ofertas.py`: função `verificar_se_ja_enviou_24h` duplicada e com lógica invertida (registrava em vez de verificar) removida; versão correta na linha ~2813 preservada

### Atualizado
- `requirements.txt` – adicionado `schedule`
- `.gitignore` – adicionados `historico_ofertas.csv`, `logs/`, padrão `cache_envios_24h*.json`
- `README.md` – documentação completa com tabela de módulos, estrutura de projeto, instruções de instalação, configuração do `.env`, execução por turnos e testes

### Removido
- `cache_envios_24h-DESKTOP-9K8H3CB.json` removido do rastreamento git (arquivo de runtime, não deve ser versionado)

---

## [1.0.0] – 2026-03-08

### Adicionado
- `rastreador_ofertas.py` – bot principal RPA: scraping Amazon, Mercado Livre, Magalu e Shopee; envio via WhatsApp Web (Selenium) e Telegram Bot API
- `TELEGRAM-WPP/telegram_bot.py` – bridge Telegram → WhatsApp
- `utils/rastreador_manual.py` – modo de envio manual via arquivo de links
- `utils/rastreador_ml.py` – scraper dedicado Mercado Livre
- `utils/promoclick_bridge.js` – sender de promoções via Telegram
- `scripts_automacao/` – scripts `.bat` por turno e por plataforma
- `docs/ESTRATEGIA_VENDAS_MANUAL.txt` – estratégia de vendas e curadoria manual
- `docs/estrategia_postagens.txt` – estratégia de postagens por nicho
- `requirements.txt` – dependências iniciais do projeto
- `.gitignore` – configuração inicial de segurança
- `README.md` – documentação inicial do projeto

---

[Unreleased]: https://github.com/debora2025-dev/smart-affiliate-bot/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/debora2025-dev/smart-affiliate-bot/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/debora2025-dev/smart-affiliate-bot/releases/tag/v1.0.0
