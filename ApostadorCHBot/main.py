import os
import logging
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from ia_adaptativa import carregar_dados, analisar_partida
from flask import Flask

# =============== CONFIGURAÇÃO ===============
TOKEN_PATH = "/workspaces/analise-ch-boot/ApostadorCHBot/.token"
with open(TOKEN_PATH, "r") as f:
    TELEGRAM_TOKEN = f.read().strip()

app_flask = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# =============== COMANDOS ===============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *CH Futebol Insights*\n\n"
        "Envie o comando:\n"
        "`/analisar TimeA x TimeB`\n\n"
        "Exemplo:\n"
        "`/analisar Corinthians x Vasco`\n\n"
        "_Base: dados reais do Brasileirão Série A 2023._",
        parse_mode="Markdown"
    )

async def analisar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando que executa a IA adaptativa."""
    try:
        texto = " ".join(context.args)
        if " x " not in texto and " X " not in texto:
            await update.message.reply_text("⚠️ Formato incorreto.\nUse: `/analisar TimeA x TimeB`", parse_mode="Markdown")
            return

        partes = texto.replace(" X ", " x ").split(" x ")
        time_casa, time_fora = partes[0].strip(), partes[1].strip()

        df = carregar_dados("/workspaces/analise-ch-boot/ApostadorCHBot/historico_2023.csv")
        resultado = analisar_partida(df, time_casa, time_fora)

        probs = resultado["probabilidades"]
        resposta = (
            f"📊 *Análise IA Adaptativa – Série A 2023*\n\n"
            f"🏠 *{time_casa}*: {probs['vitória_casa']*100:.1f}%\n"
            f"🤝 *Empate*: {probs['empate']*100:.1f}%\n"
            f"🚗 *{time_fora}*: {probs['vitória_fora']*100:.1f}%\n\n"
            f"📈 Diferença de aproveitamento: {resultado['dif_aproveitamento']:+.2f} p.p."
        )

        await update.message.reply_text(resposta, parse_mode="Markdown")

    except Exception as e:
        logging.error(e)
        await update.message.reply_text(f"❌ Erro ao processar análise: {e}")

# =============== TELEGRAM APP ===============
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("analisar", analisar))

# =============== FLASK (KEEP-ALIVE) ===============
@app_flask.route("/")
def home():
    return "🤖 CH Futebol Insights Bot rodando..."

def run_flask():
    app_flask.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_flask).start()
    print("🤖 CH Futebol Insights Bot 9.1 – IA Adaptativa integrada ⚽")
    telegram_app.run_polling()
