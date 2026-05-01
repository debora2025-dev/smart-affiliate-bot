import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE = Path(__file__).parent
VENV = BASE / ".venv"
VENV_PYTHON = VENV / "Scripts" / "python.exe"
VENV_PIP = VENV / "Scripts" / "pip.exe"

def passo(n, total, msg):
    print(f"\n[{n}/{total}] {msg}")

def ok(msg):
    print(f"  OK: {msg}")

def erro(msg):
    print(f"  ERRO: {msg}")
    input("\nPressione Enter para sair...")
    sys.exit(1)

def run(cmd, **kwargs):
    return subprocess.run(cmd, **kwargs)

print()
print("=" * 60)
print("  SMART AFFILIATE BOT - Configuracao do Ambiente")
print("  Python Setup | Versao 1.0")
print("=" * 60)

# 1. Verificar Python
passo(1, 5, "Verificando Python...")
versao = sys.version.split()[0]
ok(f"Python {versao} encontrado em: {sys.executable}")

# 2. Criar ambiente virtual
passo(2, 5, "Criando ambiente virtual (.venv)...")
if not VENV.exists():
    run([sys.executable, "-m", "venv", str(VENV)], check=True)
    ok("Ambiente virtual criado em .venv\\")
else:
    ok("Ambiente virtual ja existe.")

# 3. Instalar dependencias
passo(3, 5, "Instalando dependencias do requirements.txt...")
run([str(VENV_PIP), "install", "--upgrade", "pip", "--quiet"], check=True)
result = run([str(VENV_PIP), "install", "-r", "requirements.txt", "--quiet"])
if result.returncode != 0:
    erro("Falha ao instalar dependencias. Verifique o requirements.txt.")
ok("Todas as dependencias instaladas.")

# 4. Criar .env
passo(4, 5, "Configurando arquivo .env...")
env_file = BASE / ".env"
env_example = BASE / ".env.example"
if not env_file.exists():
    if env_example.exists():
        shutil.copy(env_example, env_file)
        ok(".env criado a partir do .env.example")
        print("  ATENCAO: Edite o .env com seus tokens antes de rodar o bot!")
    else:
        print("  AVISO: .env.example nao encontrado. Crie o .env manualmente.")
else:
    ok(".env ja existe - nao sobrescrito.")

# 5. Rodar testes
passo(5, 5, "Rodando testes de homologacao...")
result = run([str(VENV_PYTHON), "-m", "pytest",
              "testes_homologacao/teste_validador.py", "-v", "--tb=short"])
if result.returncode != 0:
    print("  AVISO: Alguns testes falharam. Verifique a saida acima.")
else:
    ok("Todos os testes passaram!")

# Instrucoes finais
print()
print("=" * 60)
print("  SETUP CONCLUIDO!")
print("=" * 60)
print()
print("  Proximos passos:")
print()
print("  1. Edite o .env com seus tokens")
print("     (Telegram, WhatsApp, Amazon Tag, etc.)")
print()
print("  2. Abra o Chrome no modo debug:")
print(r"     scripts_automacao\abrir_chrome_debug.bat")
print()
print("  3. Faca login no WhatsApp Web e nao feche o Chrome")
print()
print("  4. Execute o bot:")
print(r"     .venv\Scripts\python.exe rastreador_ofertas.py")
print()
input("Pressione Enter para sair...")
