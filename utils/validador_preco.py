"""
validador_preco.py
------------------
Validação de promoções reais com análise histórica de preços usando Pandas.
Determina se o desconto atual é genuíno ou apenas marketing.
"""

import os
import pandas as pd
from datetime import datetime, timedelta

ARQUIVO_HISTORICO = "historico_ofertas.csv"
COLUNAS = ["Data", "Produto", "Preco", "Loja"]


# ─── PERSISTÊNCIA ────────────────────────────────────────────────────────────

def _carregar_historico() -> pd.DataFrame:
    if not os.path.exists(ARQUIVO_HISTORICO):
        return pd.DataFrame(columns=COLUNAS)
    try:
        df = pd.read_csv(ARQUIVO_HISTORICO, parse_dates=["Data"])
        for col in COLUNAS:
            if col not in df.columns:
                df[col] = None
        return df
    except Exception:
        return pd.DataFrame(columns=COLUNAS)


def _salvar_historico(df: pd.DataFrame) -> None:
    df.to_csv(ARQUIVO_HISTORICO, index=False)


def registrar_preco(titulo: str, preco: float, loja: str = "") -> None:
    """Adiciona uma entrada de preço no histórico (sem duplicar no mesmo dia)."""
    if not titulo or not preco or preco <= 0:
        return

    df = _carregar_historico()
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    produto_chave = titulo.strip().lower()

    ja_existe = (
        (df["Produto"].str.lower() == produto_chave) &
        (df["Data"].astype(str).str.startswith(data_hoje))
    ).any()

    if not ja_existe:
        nova = pd.DataFrame([{
            "Data": data_hoje,
            "Produto": titulo.strip(),
            "Preco": round(float(preco), 2),
            "Loja": loja
        }])
        df = pd.concat([df, nova], ignore_index=True)
        _salvar_historico(df)


# ─── ANÁLISE ─────────────────────────────────────────────────────────────────

def analisar_preco(titulo: str, preco_atual: float, janela_dias: int = 30) -> dict:
    """
    Analisa se o preço atual é um bom negócio com base no histórico.

    Retorna um dict com:
        oportunidade   (bool)   — True se for desconto real
        veredito       (str)    — Texto curto p/ exibir na mensagem
        desconto_pct   (float)  — % de desconto em relação à média
        preco_medio    (float)  — Média histórica no período
        preco_minimo   (float)  — Menor preço já registrado
    """
    resultado = {
        "oportunidade": False,
        "veredito": "",
        "desconto_pct": 0.0,
        "preco_medio": 0.0,
        "preco_minimo": 0.0,
    }

    if not titulo or not preco_atual or preco_atual <= 0:
        return resultado

    df = _carregar_historico()
    if df.empty:
        return resultado

    produto_chave = titulo.strip().lower()
    data_corte = datetime.now() - timedelta(days=janela_dias)

    mascara = (
        (df["Produto"].str.lower() == produto_chave) &
        (pd.to_datetime(df["Data"], errors="coerce") >= data_corte)
    )
    historico = df[mascara]["Preco"].dropna().astype(float)

    if len(historico) < 2:
        return resultado

    media = round(historico.mean(), 2)
    minimo = round(historico.min(), 2)

    resultado["preco_medio"] = media
    resultado["preco_minimo"] = minimo

    if media > 0:
        desconto = round(((media - preco_atual) / media) * 100, 1)
        resultado["desconto_pct"] = desconto

        if preco_atual <= minimo * 1.02:
            resultado["oportunidade"] = True
            resultado["veredito"] = f"MENOR PREÇO DOS ÚLTIMOS {janela_dias} DIAS!"
        elif desconto >= 20:
            resultado["oportunidade"] = True
            resultado["veredito"] = f"{desconto:.0f}% ABAIXO DA MÉDIA HISTÓRICA!"
        elif desconto >= 10:
            resultado["veredito"] = f"Bom desconto: {desconto:.0f}% abaixo da média"

    return resultado


# ─── CLI DE DIAGNÓSTICO ───────────────────────────────────────────────────────

def relatorio_produto(titulo: str) -> None:
    """Imprime um relatório completo do histórico de preços de um produto."""
    df = _carregar_historico()
    if df.empty:
        print("Histórico vazio.")
        return

    produto_chave = titulo.strip().lower()
    historico = df[df["Produto"].str.lower() == produto_chave].copy()

    if historico.empty:
        print(f"Nenhum dado histórico encontrado para: {titulo}")
        return

    historico["Preco"] = historico["Preco"].astype(float)
    print(f"\n{'='*50}")
    print(f" HISTÓRICO: {titulo[:45]}")
    print(f"{'='*50}")
    print(f" Registros : {len(historico)}")
    print(f" Média     : R$ {historico['Preco'].mean():.2f}")
    print(f" Mínimo    : R$ {historico['Preco'].min():.2f}")
    print(f" Máximo    : R$ {historico['Preco'].max():.2f}")
    print(f" Último    : R$ {historico['Preco'].iloc[-1]:.2f}")
    print(f"{'='*50}\n")
    print(historico[["Data", "Preco", "Loja"]].to_string(index=False))


if __name__ == "__main__":
    # Exemplo de uso / diagnóstico manual
    import sys
    if len(sys.argv) > 1:
        relatorio_produto(" ".join(sys.argv[1:]))
    else:
        print("Uso: python validador_preco.py <nome do produto>")
