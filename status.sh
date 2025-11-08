#!/bin/bash
# 🧭 Verifica o status do Apostador CH Bot no Codespace

ROOT="/workspaces/analise-ch-boot"
LOG="$ROOT/nohup.out"

echo "🔍 Verificando status do Apostador CH Bot..."

PID=$(pgrep -f ApostadorCHBot/main.py | head -n 1)

if [ -n "$PID" ]; then
  echo "✅ Bot está em execução (PID: $PID)"
  START_TIME=$(ps -p "$PID" -o lstart=)
  echo "🕒 Iniciado em: $START_TIME"
  echo
  echo "📄 Últimas 20 linhas do log:"
  echo "---------------------------------------------"
  tail -n 20 "$LOG"
else
  echo "❌ Bot não está em execução no momento."
fi
