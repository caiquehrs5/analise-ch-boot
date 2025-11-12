#!/bin/bash
# 🚀 Script de inicialização do Analisador CH Bot (v9.0.2)
# Local: GitHub Codespace

set -e

echo "🔁 Iniciando Analisador CH Bot no Codespace..."

# Caminho do projeto
ROOT="/workspaces/analise-ch-boot"
APP="$ROOT/AnalisadorCHBot"

# Evita múltiplas instâncias simultâneas
PIDS=$(pgrep -f "$APP/main.py" || true)
if [ -n "$PIDS" ]; then
  echo "⚠️ Bot já está em execução (PIDs: $PIDS). Use stop.sh ou restart.sh antes de iniciar novamente."
  exit 0
fi

# Garante que estamos na pasta do app
cd "$APP" || { echo "❌ Pasta $APP não encontrada"; exit 1; }

# Inicia em background e direciona logs para nohup.out na raiz do repo
nohup python "$APP/main.py" > "$ROOT/nohup.out" 2>&1 &
BOT_PID=$!

sleep 2
if ! ps -p "$BOT_PID" > /dev/null 2>&1; then
  echo "❌ Falha ao iniciar o bot. Consulte $ROOT/nohup.out para detalhes."
  exit 1
fi

echo "✅ Bot iniciado em background!"
echo "📡 Logs: $ROOT/nohup.out"
echo "🛑 Para parar: pkill -f AnalisadorCHBot/main.py"
