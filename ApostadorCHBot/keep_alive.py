import os
import socket
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot Apostador CH está ativo!"


def _port_disponivel(port):
    """Retorna True se a porta estiver livre para uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", port))
        except OSError:
            return False
    return True


def _resolve_port(preferred=None):
    """Escolhe a porta para o keep_alive, caindo para uma porta livre."""
    candidates = [
        preferred,
        os.environ.get("KEEP_ALIVE_PORT"),
        os.environ.get("PORT"),
        5000,
    ]

    for value in candidates:
        if not value:
            continue
        try:
            port = int(value)
        except (TypeError, ValueError):
            continue
        if 0 < port < 65536 and _port_disponivel(port):
            return port

    # Se nenhuma porta explícita for válida, use uma porta aleatória livre.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


def run():
    port = _resolve_port()
    while True:
        try:
            app.run(host='0.0.0.0', port=port, use_reloader=False)
            break
        except OSError as exc:
            print(f"[keep_alive] Porta {port} indisponível ({exc}), tentando porta alternativa.")
            port = _resolve_port()

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()
