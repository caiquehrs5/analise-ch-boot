"""
Módulo: data_pipeline.py
Versão: 8.2 – CH Futebol Insights Bot
Descrição:
    Coleta automática de dados do Brasileirão via API-Football
    com fallback para dataset público (GitHub) caso a API esteja indisponível.
"""

import os
import json
import time
import logging
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# ===============================
# CONFIGURAÇÕES GERAIS
# ===============================

load_dotenv()
API_URL = "https://v3.football.api-sports.io"
API_KEY = os.getenv("API_FOOTBALL_KEY", "demo")

# IDs padrão
BRASILEIRAO_ID = 71
SEASON = 2025

# Diretórios
RAW_DIR = "data/raw"
CLEAN_DIR = "data/clean"
LOG_DIR = "logs"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CLEAN_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Configuração de logs
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "data_pipeline.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("CH_Futebol_Insights")

def registrar_log(msg):
    logger.info(msg)
    print(f"📘 {msg}")

# ===============================
# REQUISIÇÃO À API
# ===============================

def requisitar_dados(endpoint, params):
    headers = {"x-apisports-key": API_KEY}
    try:
        resp = requests.get(f"{API_URL}/{endpoint}", headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            registrar_log(f"⚠️ Erro {resp.status_code} ao acessar endpoint {endpoint}.")
            return {}
    except Exception as e:
        registrar_log(f"❌ Falha de conexão com API: {e}")
        return {}

# ===============================
# PROCESSAMENTO DE PARTIDAS
# ===============================

def processar_partidas(dados_json):
    partidas = dados_json.get("response", [])
    registros = []
    for j in partidas:
        try:
            registros.append({
                "data": j["fixture"]["date"].split("T")[0],
                "casa": j["teams"]["home"]["name"],
                "fora": j["teams"]["away"]["name"],
                "gols_casa": j["goals"]["home"],
                "gols_fora": j["goals"]["away"],
                "status": j["fixture"]["status"]["long"],
            })
        except KeyError:
            continue
    return pd.DataFrame(registros)

# ===============================
# FALLBACK AUTOMÁTICO: DATASET PÚBLICO
# ===============================

def baixar_dataset_publico():
    url = "https://raw.githubusercontent.com/henriquebastos/brasileirao-dataset/master/data/brasileirao.csv"
    destino = os.path.join(CLEAN_DIR, "fixtures_brasileirao_local.csv")
    try:
        registrar_log("🧠 Baixando dataset público do GitHub (henriquebastos/brasileirao-dataset)...")
        df = pd.read_csv(url)
        df.to_csv(destino, index=False, encoding="utf-8-sig")
        registrar_log(f"✅ Dataset público salvo com sucesso em {destino}")
    except Exception as e:
        registrar_log(f"❌ Falha ao baixar dataset público: {e}")

# ===============================
# PIPELINE PRINCIPAL
# ===============================

def iniciar_pipeline():
    registrar_log("🚀 Iniciando pipeline de dados do Brasileirão Série A 2025...")
    cache_path = os.path.join(RAW_DIR, "fixtures_brasileirao_2025.json")

    dados = requisitar_dados("fixtures", {"league": BRASILEIRAO_ID, "season": SEASON})

    if not dados or not dados.get("response"):
        registrar_log("⚠️ API indisponível. Ativando fallback automático para dataset público...")
        baixar_dataset_publico()
        return

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    registrar_log(f"💾 Dados da API salvos em {cache_path}")

    df = processar_partidas(dados)
    df.to_csv(os.path.join(CLEAN_DIR, "fixtures_brasileirao_2025.csv"), index=False, encoding="utf-8-sig")
    registrar_log(f"✅ Pipeline finalizado com sucesso. Dados prontos para análise.")

# ===============================
# EXECUÇÃO DIRETA
# ===============================
if __name__ == "__main__":
    iniciar_pipeline()
