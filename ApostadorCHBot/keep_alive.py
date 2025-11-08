from flask import Flask
import threading
import logging

app = Flask(__name__)
logger = logging.getLogger("KeepAlive")

@app.route("/")
def home():
    return "🟢 CH Bot v9.3.4 Final está ativo e servindo Flask Keep-Alive!"

def iniciar_servidor():
    """Inicia o servidor Flask em thread independente"""
    try:
        logger.info("🌐 Iniciando servidor Flask Keep-Alive (porta 5000)...")
        app.run(host="0.0.0.0", port=5000)
    except Exception as e:
        logger.error(f"Erro no servidor Flask: {e}")
