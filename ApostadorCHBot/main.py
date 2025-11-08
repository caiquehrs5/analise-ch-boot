import logging
import threading
import time
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)
from ia_adaptativa import processar_mensagem
from keep_alive import iniciar_servidor
import os

# ==========================================
# CONFIGURAÇÃO DE LOGS COLORIDOS E DETALHADOS
# ==========================================
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] → %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("CHBot")

# ==========================================
# VARIÁVEIS PRINCIPAIS
# ==========================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8302402604:AAE0l2ibTxyIf5fFWbdn7WTJpCYqkMHYyYM")
START_TIME = time.time()


# ==========================================
# COMANDOS DO BOT
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Boas-vindas"""
    uptime = time.strftime("%Hh %Mm %Ss", time.gmtime(time.time() - START_TIME))
    await update.message.reply_text(
        f"👋 Olá, {update.effective_user.first_name}!\n"
        f"🤖 CH Bot v9.3.4 Final está online!\n"
        f"⏱ Uptime: {uptime}\n"
        f"Envie /analisar para processar uma partida com IA adaptativa ⚽"
    )
    logger.info("Comando /start recebido — Bot operacional.")


async def analisar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /analisar — executa IA adaptativa"""
    try:
        inicio = time.time()
        await update.message.reply_text("🔍 Iniciando análise inteligente...")
        resposta = processar_mensagem("Analisar últimas partidas Brasileirão 2025")
        fim = time.time()
        tempo = round(fim - inicio, 2)
        await update.message.reply_text(f"✅ Análise concluída em {tempo}s:\n\n{resposta}")
        logger.info(f"Análise finalizada com sucesso em {tempo}s")
    except Exception as e:
        logger.error(f"Erro durante análise: {e}")
        await update.message.reply_text("⚠️ Erro temporário ao processar a análise. Tente novamente mais tarde.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status — métricas e estado"""
    uptime = time.strftime("%Hh %Mm %Ss", time.gmtime(time.time() - START_TIME))
    await update.message.reply_text(
        f"🟢 CH Bot v9.3.4 Final ativo!\n"
        f"⏱ Uptime: {uptime}\n"
        f"📡 API: SportMonks + IA adaptativa"
    )
    logger.info("Status solicitado pelo usuário.")


# ==========================================
# INICIALIZAÇÃO DO BOT
# ==========================================
def iniciar_bot():
    """Inicializa o polling do bot com auto-restart"""
    while True:
        try:
            logger.info("🚀 Iniciando CH Bot v9.3.4 Final (Polling + Flask Threads)...")
            app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("analisar", analisar))
            app.add_handler(CommandHandler("status", status))

            # Inicia Flask keep-alive em thread separada
            flask_thread = threading.Thread(target=iniciar_servidor)
            flask_thread.daemon = True
            flask_thread.start()

            logger.info("✅ Threads iniciadas (Bot + Flask).")
            app.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"❌ Falha no bot: {e}")
            logger.info("🔁 Reiniciando em 5 segundos...")
            time.sleep(5)


if __name__ == "__main__":
    iniciar_bot()
