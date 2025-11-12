#!/bin/bash
# 🛑 Encerra o Analisador CH Bot no Codespace

echo "🛑 Encerrando Analisador CH Bot..."

PIDS=$(pgrep -f AnalisadorCHBot/main.py || true)

if [ -z "$PIDS" ]; then
  echo "⚠️ Nenhum processo ativo encontrado."
  exit 0
fi

for PID in $PIDS; do
  if kill "$PID" 2>/dev/null; then
    sleep 1
    if ps -p "$PID" > /dev/null 2>&1; then
      kill -9 "$PID" 2>/dev/null || true
    fi
    echo "✅ Processo (PID: $PID) encerrado com sucesso!"
  else
    echo "⚠️ Não foi possível encerrar o PID $PID (talvez já finalizado)."
  fi
done
