"""
logger.py
---------
Sistema de logging centralizado para o Smart Affiliate Bot.
Substitui os print() espalhados pelo código por logs estruturados
que são gravados em arquivo e exibidos no console simultaneamente.
"""

import logging
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, f"bot_{datetime.now().strftime('%Y-%m-%d')}.log")

_logger_configurado = False


def _configurar() -> logging.Logger:
    global _logger_configurado

    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("smart_affiliate_bot")

    if _logger_configurado:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler de arquivo (tudo a partir de DEBUG)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # Handler de console (só INFO e acima)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    _logger_configurado = True
    return logger


# ─── API PÚBLICA ──────────────────────────────────────────────────────────────

def get_logger() -> logging.Logger:
    return _configurar()


def info(msg: str) -> None:
    _configurar().info(msg)


def debug(msg: str) -> None:
    _configurar().debug(msg)


def warning(msg: str) -> None:
    _configurar().warning(msg)


def error(msg: str) -> None:
    _configurar().error(msg)


def sucesso(msg: str) -> None:
    """Atalho semântico: INFO com prefixo ✅"""
    _configurar().info(f"✅ {msg}")


def falha(msg: str) -> None:
    """Atalho semântico: ERROR com prefixo ❌"""
    _configurar().error(f"❌ {msg}")


def alerta(msg: str) -> None:
    """Atalho semântico: WARNING com prefixo ⚠️"""
    _configurar().warning(f"⚠️  {msg}")


# ─── EXEMPLO DE USO ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    info("Bot iniciado")
    debug("Modo debug ativo")
    sucesso("Oferta enviada para o grupo")
    alerta("Imagem não encontrada, enviando só texto")
    falha("Timeout ao conectar ao WhatsApp Web")
    print(f"\nLog salvo em: {LOG_FILE}")
