from flask import Flask
import threading
import logging
print("🔁 Executando versão atualizada do keep_alive.py")


app = Flask(__name__)
logger = logging.getLogger("KeepAlive")

@app.route("/")

def iniciar_servidor():
    """Inicia o servidor Flask em thread independente"""
    for porta in range(5000, 5010):  # tenta da 5000 até 5009
        try:
            logger.info(f"🌐 Iniciando servidor Flask Keep-Alive (porta {porta})...")
            app.run(host='0.0.0.0', port=porta)
            break  # Sai do loop se o servidor iniciar com sucesso
        except OSError:
            logger.warning(f"⚠️ Porta {porta} ocupada, tentando próxima...")
            continue
        except Exception as e:
            logger.error(f"❌ Erro no servidor Flask: {e}")
            break


