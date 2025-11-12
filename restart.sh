#!/bin/bash
# ♻️ Reinicia o Analisador CH Bot no Codespace
# Autor: Carlos Henrique (CH)
# Versão: 9.0.2

echo "♻️ Reiniciando Analisador CH Bot..."

ROOT="/workspaces/analise-ch-boot"
APP="$ROOT/AnalisadorCHBot"

# Passo 1: Parar bot existente
PIDS=$(pgrep -f AnalisadorCHBot/main.py || true)
if [ -n "$PIDS" ]; then
  for PID in $PIDS; do
    echo "🛑 Encerrando processo existente (PID: $PID)..."
    kill "$PID" 2>/dev/null || true
    sleep 1
    if ps -p "$PID" > /dev/null 2>&1; then
      kill -9 "$PID" 2>/dev/null || true
    fi
  done
  echo "✅ Bot parado com sucesso."
else
  echo "⚠️ Nenhum processo ativo encontrado — iniciando do zero."
fi

# Passo 2: Iniciar novamente
cd "$APP" || { echo "❌ Pasta $APP não encontrada"; exit 1; }
nohup python "$APP/main.py" > "$ROOT/nohup.out" 2>&1 &
sleep 3

NEW_PIDS=$(pgrep -f AnalisadorCHBot/main.py || true)

echo "🚀 Analisador CH Bot reiniciado com sucesso!"
echo "🆕 Novo(s) PID(s): ${NEW_PIDS:-indisponível}"
echo "📡 Logs: $ROOT/nohup.out"
