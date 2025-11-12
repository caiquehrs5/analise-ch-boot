#!/bin/bash
# 🧭 Verifica o status do Analisador CH Bot no Codespace

ROOT="/workspaces/analise-ch-boot"
LOG="$ROOT/nohup.out"

echo "🔍 Verificando status do Analisador CH Bot..."

PIDS=$(pgrep -f AnalisadorCHBot/main.py || true)

if [ -n "$PIDS" ]; then
  echo "✅ Bot está em execução (PID(s): $(echo "$PIDS" | tr '\n' ' '))"
  FIRST_PID=$(echo "$PIDS" | head -n 1)
  START_TIME=$(ps -p "$FIRST_PID" -o lstart=)
  echo "🕒 Iniciado em: $START_TIME"
  echo
  echo "📄 Últimas 20 linhas do log:"
  echo "---------------------------------------------"
  tail -n 20 "$LOG"
else
  echo "❌ Bot não está em execução no momento."
fi
