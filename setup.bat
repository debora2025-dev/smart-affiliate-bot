@echo off
chcp 65001 >nul
title Smart Affiliate Bot – Setup Inicial
color 0A

echo.
echo  ============================================================
echo   SMART AFFILIATE BOT – Configuracao do Ambiente
echo   Versao 1.0 ^| Python 3.13 + Selenium + Pandas
echo  ============================================================
echo.

:: ------------------------------------------------------------------
:: 1. Verificar Python
:: ------------------------------------------------------------------
echo [1/6] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERRO: Python nao encontrado. Instale em https://python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do set PYVER=%%V
echo  OK: %PYVER%

:: ------------------------------------------------------------------
:: 2. Criar ambiente virtual
:: ------------------------------------------------------------------
echo.
echo [2/6] Criando ambiente virtual (.venv)...
if not exist ".venv" (
    python -m venv .venv
    echo  OK: Ambiente virtual criado em .venv\
) else (
    echo  OK: Ambiente virtual ja existe.
)

:: ------------------------------------------------------------------
:: 3. Ativar venv e instalar dependências
:: ------------------------------------------------------------------
echo.
echo [3/6] Instalando dependencias do requirements.txt...
call .venv\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo  OK: Todas as dependencias instaladas.

:: ------------------------------------------------------------------
:: 4. Criar .env a partir do .env.example
:: ------------------------------------------------------------------
echo.
echo [4/6] Configurando arquivo .env...
if not exist ".env" (
    copy .env.example .env >nul
    echo  OK: .env criado a partir do .env.example
    echo  ATENCAO: Edite o arquivo .env com seus tokens antes de executar o bot!
) else (
    echo  OK: .env ja existe - nao sobrescrito.
)

:: ------------------------------------------------------------------
:: 5. Rodar testes de homologacao
:: ------------------------------------------------------------------
echo.
echo [5/6] Rodando testes de homologacao...
python -m pytest testes_homologacao\teste_validador.py -v --tb=short 2>&1
if errorlevel 1 (
    echo  AVISO: Alguns testes falharam. Verifique a saida acima.
) else (
    echo  OK: Todos os testes passaram!
)

:: ------------------------------------------------------------------
:: 6. Instruções finais
:: ------------------------------------------------------------------
echo.
echo  ============================================================
echo   SETUP CONCLUIDO!
echo  ============================================================
echo.
echo  Proximos passos:
echo.
echo   1. Edite o arquivo .env com seus tokens e configuracoes
echo      (Telegram, WhatsApp, Amazon Tag, etc.)
echo.
echo   2. Inicie o Chrome no modo debug:
echo      chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\ChromeBot
echo.
echo   3. Execute o bot principal:
echo      python rastreador_ofertas.py
echo.
echo   4. Ou use o agendador automatico (executa nos turnos do dia):
echo      python utils\agendador.py
echo.
echo   Para ver os turnos agendados:
echo      python utils\agendador.py --listar
echo.
pause
