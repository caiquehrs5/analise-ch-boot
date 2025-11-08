#!/bin/bash
# ♻️ Reinicia o Apostador CH Bot no Codespace
# Autor: Carlos Henrique (CH)
# Versão: 9.0.2

echo "♻️ Reiniciando Apostador CH Bot..."

ROOT="/workspaces/analise-ch-boot"
APP="$ROOT/ApostadorCHBot"

# Passo 1: Parar bot existente
PID=$(pgrep -f ApostadorCHBot/main.py | head -n 1)
if [ -n "$PID" ]; then
  echo "🛑 Encerrando processo existente (PID: $PID)..."
  kill "$PID"
  sleep 2
  echo "✅ Bot parado com sucesso."
else
  echo "⚠️ Nenhum processo ativo encontrado — iniciando do zero."
fi

# Passo 2: Iniciar novamente
cd "$APP" || { echo "❌ Pasta $APP não encontrada"; exit 1; }
nohup python main.py > "$ROOT/nohup.out" 2>&1 &
sleep 3

NEW_PID=$(pgrep -f ApostadorCHBot/main.py | head -n 1)

echo "🚀 Apostador CH Bot reiniciado com sucesso!"
echo "🆕 Novo PID: $NEW_PID"
echo "📡 Logs: $ROOT/nohup.out"
