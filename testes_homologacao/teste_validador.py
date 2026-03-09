"""
teste_validador.py
------------------
Testes automatizados para utils/validador_preco.py.
Verifica se a análise histórica de preços está funcionando corretamente.

Uso: python testes_homologacao/teste_validador.py
"""

import sys
import os
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Usa um arquivo de histórico temporário para não contaminar dados reais
HIST_TEMP = "historico_teste_temp.csv"
import utils.validador_preco as v
v.ARQUIVO_HISTORICO = HIST_TEMP


def limpar():
    if os.path.exists(HIST_TEMP):
        os.remove(HIST_TEMP)


def _ok(descricao: str):
    print(f"  ✅ {descricao}")


def _falha(descricao: str, detalhe: str = ""):
    print(f"  ❌ {descricao}" + (f" — {detalhe}" if detalhe else ""))
    sys.exit(1)


# ─── TESTES ──────────────────────────────────────────────────────────────────

def teste_historico_vazio():
    """Sem histórico, analisar_preco deve retornar oportunidade=False."""
    limpar()
    res = v.analisar_preco("Produto Teste", 100.0)
    assert not res["oportunidade"], "Esperava oportunidade=False"
    assert res["preco_medio"] == 0.0
    _ok("Histórico vazio não gera falso positivo")


def teste_registro_sem_duplicata():
    """Registrar o mesmo produto no mesmo dia duas vezes não deve criar duplicata."""
    limpar()
    v.registrar_preco("Fone JBL Tune 510BT", 199.90, "Amazon")
    v.registrar_preco("Fone JBL Tune 510BT", 199.90, "Amazon")  # duplicata
    df = v._carregar_historico()
    count = (df["Produto"].str.lower() == "fone jbl tune 510bt").sum()
    assert count == 1, f"Esperava 1 registro, encontrou {count}"
    _ok("Duplicata no mesmo dia bloqueada")


def teste_desconto_genuino():
    """Produto com preço atual 30% abaixo da média histórica deve ser marcado como oportunidade."""
    limpar()
    from datetime import datetime, timedelta
    import pandas as pd

    # Simula 10 registros históricos a R$ 200,00
    registros = []
    for i in range(10):
        data = (datetime.now() - timedelta(days=i + 1)).strftime("%Y-%m-%d")
        registros.append({"Data": data, "Produto": "Notebook Dell", "Preco": 200.0, "Loja": "Magalu"})

    pd.DataFrame(registros).to_csv(HIST_TEMP, index=False)

    res = v.analisar_preco("Notebook Dell", 130.0)  # 35% abaixo da média

    assert res["oportunidade"], "Esperava oportunidade=True"
    assert res["desconto_pct"] >= 20, f"Desconto esperado >= 20%, obteve {res['desconto_pct']}"
    _ok(f"Desconto genuíno detectado ({res['desconto_pct']:.1f}% abaixo da média)")


def teste_preco_normal_sem_alerta():
    """Produto com preço dentro da média histórica não deve gerar alerta."""
    limpar()
    from datetime import datetime, timedelta
    import pandas as pd

    registros = []
    for i in range(5):
        data = (datetime.now() - timedelta(days=i + 1)).strftime("%Y-%m-%d")
        registros.append({"Data": data, "Produto": "Mouse Logitech G203", "Preco": 150.0, "Loja": "ML"})

    pd.DataFrame(registros).to_csv(HIST_TEMP, index=False)

    res = v.analisar_preco("Mouse Logitech G203", 148.0)  # Praticamente igual à média

    assert not res["oportunidade"], "Esperava oportunidade=False para preço normal"
    _ok("Preço normal não gera alerta falso")


def teste_menor_preco_historico():
    """Produto no mínimo histórico deve ser marcado com veredito especial."""
    limpar()
    from datetime import datetime, timedelta
    import pandas as pd

    registros = [
        {"Data": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"), "Produto": "Air Fryer Mondial", "Preco": 350.0, "Loja": "Magalu"},
        {"Data": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"), "Produto": "Air Fryer Mondial", "Preco": 320.0, "Loja": "Magalu"},
        {"Data": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), "Produto": "Air Fryer Mondial", "Preco": 300.0, "Loja": "Magalu"},
    ]
    pd.DataFrame(registros).to_csv(HIST_TEMP, index=False)

    res = v.analisar_preco("Air Fryer Mondial", 299.0)  # Abaixo do mínimo

    assert res["oportunidade"], "Esperava oportunidade=True no mínimo histórico"
    assert "MENOR PREÇO" in res["veredito"], f"Veredito inesperado: {res['veredito']}"
    _ok(f"Mínimo histórico detectado: {res['veredito']}")


# ─── RUNNER ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  TESTES — validador_preco.py")
    print("=" * 50)

    testes = [
        teste_historico_vazio,
        teste_registro_sem_duplicata,
        teste_desconto_genuino,
        teste_preco_normal_sem_alerta,
        teste_menor_preco_historico,
    ]

    for teste in testes:
        try:
            teste()
        except AssertionError as e:
            _falha(teste.__name__, str(e))
        except Exception as e:
            _falha(teste.__name__, f"Exceção inesperada: {e}")

    limpar()
    print("\n" + "=" * 50)
    print(f"  {len(testes)}/{len(testes)} testes passaram ✅")
    print("=" * 50 + "\n")
