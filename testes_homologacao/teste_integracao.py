"""
Teste de Integração – Smart Affiliate Bot
Valida que todos os módulos do projeto importam e funcionam corretamente.
Não depende de Chrome, Selenium ou conexão externa.
"""
import sys
import os
import importlib

# Garante que o root do projeto está no path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


# ─── 1. IMPORTAÇÕES DOS MÓDULOS UTILS ────────────────────────────────────────

def test_import_validador_preco():
    """utils/validador_preco.py deve importar sem erros"""
    mod = importlib.import_module("utils.validador_preco")
    assert hasattr(mod, "registrar_preco"), "Falta função registrar_preco"
    assert hasattr(mod, "analisar_preco"), "Falta função analisar_preco"
    assert hasattr(mod, "relatorio_produto"), "Falta função relatorio_produto"


def test_import_logger():
    """utils/logger.py deve importar sem erros"""
    mod = importlib.import_module("utils.logger")
    for fn in ("info", "debug", "warning", "error", "sucesso", "falha", "alerta"):
        assert hasattr(mod, fn), f"Falta função {fn} no logger"


def test_import_agendador():
    """utils/agendador.py deve importar sem erros"""
    mod = importlib.import_module("utils.agendador")
    assert hasattr(mod, "agendar_todos"), "Falta função agendar_todos"


# ─── 2. DEPENDÊNCIAS EXTERNAS ────────────────────────────────────────────────

def test_dependencias_instaladas():
    """Todos os pacotes do requirements.txt devem estar instalados"""
    pacotes = [
        ("requests", "requests"),
        ("pandas", "pandas"),
        ("bs4", "beautifulsoup4"),
        ("selenium", "selenium"),
        ("dotenv", "python-dotenv"),
        ("schedule", "schedule"),
        ("PIL", "pillow"),
    ]
    faltando = []
    for modulo, nome_pip in pacotes:
        try:
            importlib.import_module(modulo)
        except ImportError:
            faltando.append(nome_pip)

    assert not faltando, f"Pacotes não instalados: {', '.join(faltando)}\nRode: pip install -r requirements.txt"


# ─── 3. ARQUIVOS ESSENCIAIS ───────────────────────────────────────────────────

def test_arquivos_essenciais_existem():
    """Todos os arquivos essenciais do projeto devem existir"""
    arquivos = [
        "rastreador_ofertas.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "utils/validador_preco.py",
        "utils/logger.py",
        "utils/agendador.py",
        "links.txt.example",
        "shopee_links.txt.example",
    ]
    faltando = [f for f in arquivos if not os.path.exists(os.path.join(ROOT, f))]
    assert not faltando, f"Arquivos ausentes: {', '.join(faltando)}"


def test_env_example_tem_chaves_obrigatorias():
    """O .env.example deve conter as chaves de configuração mínimas"""
    env_path = os.path.join(ROOT, ".env.example")
    assert os.path.exists(env_path), ".env.example não encontrado"

    with open(env_path, encoding="utf-8") as f:
        conteudo = f.read()

    chaves_obrigatorias = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "GRUPO_WHATSAPP",
        "CHROME_DEBUG_PORT",
    ]
    faltando = [k for k in chaves_obrigatorias if k not in conteudo]
    assert not faltando, f"Chaves ausentes no .env.example: {', '.join(faltando)}"


# ─── 4. LÓGICA DO VALIDADOR ──────────────────────────────────────────────────

def test_validador_retorna_estrutura_correta():
    """analisar_preco deve retornar dict com as chaves esperadas"""
    from utils.validador_preco import analisar_preco

    resultado = analisar_preco("Produto Teste XYZ", 99.90)

    chaves_esperadas = {"oportunidade", "veredito", "desconto_pct", "preco_medio", "preco_minimo"}
    assert isinstance(resultado, dict), "Deve retornar um dicionário"
    assert chaves_esperadas.issubset(resultado.keys()), (
        f"Chaves ausentes: {chaves_esperadas - resultado.keys()}"
    )


def test_validador_sem_historico_retorna_sem_dados():
    """Produto sem histórico deve retornar veredito de 'sem dados'"""
    from utils.validador_preco import analisar_preco

    # Título muito específico que certamente não existe no histórico
    resultado = analisar_preco("ProdutoTesteIntegracao_XYZ_12345_Inexistente", 100.00)
    assert resultado["oportunidade"] is False, "Sem histórico não deve ser marcado como oportunidade"
    assert resultado["preco_medio"] == 0.0, "Sem histórico, preco_medio deve ser 0.0"


# ─── 5. LOGGER ────────────────────────────────────────────────────────────────

def test_logger_nao_lanca_excecao():
    """As funções de logging não devem lançar exceções"""
    from utils import logger

    # Deve executar sem erros (pode criar arquivo de log)
    logger.info("Teste de integração – info")
    logger.sucesso("Teste de integração – sucesso")
    logger.error("Teste de integração – erro (esperado em teste)")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
