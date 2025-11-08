#!/bin/bash
# 🚀 Script de inicialização do Apostador CH Bot (v9.0.2)
# Local: GitHub Codespace

set -e

echo "🔁 Iniciando Apostador CH Bot no Codespace..."

# Caminho do projeto
ROOT="/workspaces/analise-ch-boot"
APP="$ROOT/ApostadorCHBot"

# Garante que estamos na pasta do app
cd "$APP" || { echo "❌ Pasta $APP não encontrada"; exit 1; }

# Inicia em background e direciona logs para nohup.out na raiz do repo
nohup python main.py > "$ROOT/nohup.out" 2>&1 &

sleep 2
echo "✅ Bot iniciado em background!"
echo "📡 Logs: $ROOT/nohup.out"
echo "🛑 Para parar: pkill -f ApostadorCHBot/main.py"
