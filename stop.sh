#!/bin/bash
# 🛑 Encerra o Apostador CH Bot no Codespace

echo "🛑 Encerrando Apostador CH Bot..."

PID=$(pgrep -f ApostadorCHBot/main.py | head -n 1)

if [ -n "$PID" ]; then
  kill "$PID"
  echo "✅ Processo (PID: $PID) encerrado com sucesso!"
else
  echo "⚠️ Nenhum processo ativo encontrado."
fi
