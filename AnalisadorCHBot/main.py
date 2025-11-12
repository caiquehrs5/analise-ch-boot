import asyncio
import logging
import threading
import time
from dotenv import load_dotenv
import os

# Carregar variáveis do arquivo .env
load_dotenv()

from flask import Flask
from telegram import Update
from telegram.error import InvalidToken
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)
from ia_adaptativa import processar_mensagem
from keep_alive import iniciar_servidor
import os
from typing import Optional

# ==========================================
# CONFIGURAÇÃO DE LOGS COLORIDOS E DETALHADOS
# ==========================================
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] → %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("AnalisadorCHBot")

# ==========================================
# VARIÁVEIS PRINCIPAIS
# ==========================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    logger.error("Variável de ambiente TELEGRAM_TOKEN não definida. Abortando.")
    raise SystemExit("TELEGRAM_TOKEN não informada!")

START_TIME = time.time()
_flask_thread: Optional[threading.Thread] = None

# ==========================================
# COMANDOS DO BOT
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start - Boas-vindas"""
    uptime = time.strftime("%Hh %Mm %Ss", time.gmtime(time.time() - START_TIME))
    logger.info(f"Comando /start pelo usuário: {update.effective_user.id}")
    await update.message.reply_text(
        f"👋 Olá, {update.effective_user.first_name}!\n"
        f"🤖 Analisador CH Bot v9.3.4 Final está online!\n"
        f"⏱ Uptime: {uptime}\n"
        f"Envie /analisar para processar uma partida com IA adaptativa ⚽"
    )
    logger.info("Fim do comando /start")

async def analisar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /analisar — executa IA adaptativa"""
    try:
        inicio = time.time()
        logger.info(f"Comando /analisar pelo usuário: {update.effective_user.id}")
        partida = ' '.join(context.args) if context.args else "Analisar últimas partidas Brasileirão 2025"
        await update.message.reply_text(f"🔎 Iniciando análise inteligente para: {partida}...")
        resposta = processar_mensagem(partida)
        fim = time.time()
        tempo = round(fim - inicio, 2)
        await update.message.reply_text(f"✅ Análise concluída em {tempo}s:\n\n{resposta}")
        logger.info(f"Fim do comando /analisar em {tempo}s")
    except Exception as e:
        logger.error(f"Erro durante análise: {e}")
        await update.message.reply_text("⚠️ Erro temporário ao processar a análise. Tente novamente mais tarde.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /status — métricas e estado"""
    uptime = time.strftime("%Hh %Mm %Ss", time.gmtime(time.time() - START_TIME))
    logger.info(f"Comando /status pelo usuário: {update.effective_user.id}")
    await update.message.reply_text(
        f"🟢 Analisador CH Bot v9.3.4 Final ativo!\n"
        f"⏱ Uptime: {uptime}\n"
        f"📡 API: SportMonks + IA adaptativa"
    )
    logger.info("Fim do comando /status")

# ==========================================
# INICIALIZAÇÃO DO BOT
# ==========================================
def iniciar_keep_alive_thread() -> None:
    """Garante apenas uma instância do servidor Flask keep-alive."""
    global _flask_thread
    if _flask_thread and _flask_thread.is_alive():
        return
    _flask_thread = threading.Thread(target=iniciar_servidor, name="KeepAliveServer", daemon=True)
    _flask_thread.start()
    logger.info("🌐 Thread Flask Keep-Alive ativa.")


def iniciar_bot() -> None:
    """Inicializa o polling do bot com auto-restart"""
    iniciar_keep_alive_thread()
    while True:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            logger.info("🚀 Iniciando Analisador CH Bot v9.3.4 Final (Polling + Flask Threads)...")
            app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("analisar", analisar))
            app.add_handler(CommandHandler("status", status))

            logger.info("✅ Threads iniciadas (Bot + Flask).")
            app.run_polling(allowed_updates=Update.ALL_TYPES)
        except InvalidToken:
            logger.error("❌ TELEGRAM_TOKEN rejeitado pela API. Atualize o token e reinicie o bot.")
            break
        except Exception as e:
            logger.error(f"❌ Falha no bot: {e}")
            logger.info("🔁 Reiniciando em 5 segundos...")
            time.sleep(5)

if __name__ == "__main__":
    iniciar_bot()
