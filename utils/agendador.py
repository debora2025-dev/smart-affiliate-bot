"""
agendador.py
------------
Agendador automático dos turnos do Smart Affiliate Bot.
Substitui os arquivos .bat por um scheduler Python puro,
com suporte a horários configuráveis e log de execução.

Uso:
    python utils/agendador.py          # Roda o agendador continuamente
    python utils/agendador.py --listar # Lista os próximos agendamentos
"""

import subprocess
import sys
import os
import time
import schedule
from datetime import datetime

# ─── CONFIGURAÇÃO DOS TURNOS ─────────────────────────────────────────────────
# Edite os horários e argumentos conforme sua estratégia de postagem.

PYTHON = sys.executable
SCRIPT_PRINCIPAL = os.path.join(os.path.dirname(__file__), "..", "rastreador_ofertas.py")

TURNOS = [
    {
        "nome": "Manhã",
        "horario": "09:00",
        "argumento": "MANHA",
        "descricao": "Eletroportáteis, Beleza, Achadinhos Shopee",
    },
    {
        "nome": "Almoço",
        "horario": "12:30",
        "argumento": "ALMOCO",
        "descricao": "Celulares, Games, Mercado Livre",
    },
    {
        "nome": "Tarde",
        "horario": "15:30",
        "argumento": "TARDE",
        "descricao": "Notebooks, Periféricos, Áudio",
    },
    {
        "nome": "Noite",
        "horario": "20:00",
        "argumento": "NOITE",
        "descricao": "TVs, Eletrodomésticos, PC Gamer",
    },
    {
        "nome": "Cupons",
        "horario": "09:15",
        "argumento": "--cupons",
        "descricao": "Ativação de cupons do Magalu",
    },
    {
        "nome": "Feminino",
        "horario": "10:00",
        "argumento": "MULHER",
        "descricao": "Foco em público feminino (ticket baixo)",
    },
]


# ─── EXECUTOR ────────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def executar_turno(turno: dict) -> None:
    _log(f"▶ Iniciando turno '{turno['nome']}' ({turno['descricao']})")

    cmd = [PYTHON, os.path.abspath(SCRIPT_PRINCIPAL), turno["argumento"]]
    try:
        proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)
        _log(f"  PID {proc.pid} — aguardando conclusão...")
        proc.wait()
        _log(f"✅ Turno '{turno['nome']}' concluído (código {proc.returncode})")
    except FileNotFoundError:
        _log(f"❌ Script não encontrado: {SCRIPT_PRINCIPAL}")
    except Exception as e:
        _log(f"❌ Erro ao executar '{turno['nome']}': {e}")


# ─── AGENDAMENTO ─────────────────────────────────────────────────────────────

def agendar_todos() -> None:
    for turno in TURNOS:
        t = turno.copy()
        schedule.every().day.at(t["horario"]).do(executar_turno, turno=t)
        _log(f"  📅 '{t['nome']}' agendado para {t['horario']} todos os dias")


def listar_agendamentos() -> None:
    print("\n" + "=" * 52)
    print("  AGENDAMENTOS DO SMART AFFILIATE BOT")
    print("=" * 52)
    for turno in TURNOS:
        print(f"  {turno['horario']}  |  {turno['nome']:<10}  |  {turno['descricao']}")
    print("=" * 52 + "\n")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main() -> None:
    if "--listar" in sys.argv:
        listar_agendamentos()
        return

    _log("🤖 Agendador do Smart Affiliate Bot iniciado")
    agendar_todos()
    listar_agendamentos()

    _log("⏳ Aguardando horários agendados... (Ctrl+C para parar)")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        _log("🛑 Agendador encerrado pelo usuário.")
