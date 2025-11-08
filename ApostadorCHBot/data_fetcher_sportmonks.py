# -*- coding: utf-8 -*-
import requests
import pandas as pd
import time

TOKEN = "IrTQK9UlTuwS5goNh6zQruXlpZTxcUtM11RoPwsd31Y26e9x2e73oufBS5HC"
BASE_URL = f"https://api.sportmonks.com/v3/football"
COUNTRY_ID = 17  # Brasil

def validar_token():
    """Valida o token e checa se retorna dados válidos"""
    print("🔍 Validando token e listando ligas do Brasil...")
    url = f"{BASE_URL}/leagues/countries/{COUNTRY_ID}?api_token={TOKEN}"
    inicio = time.time()
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if not data:
                print("⚠️ Nenhuma liga encontrada para o Brasil.")
                return False
            print(f"✅ Token válido! {len(data)} ligas encontradas:")
            for l in data[:5]:
                print(f"   ⚽ {l['name']} (ID: {l['id']})")
            print(f"⏱️ Finalizado em {time.time()-inicio:.2f}s")
            return True
        elif r.status_code == 401:
            print("❌ Token inválido ou expirado (401).")
        elif r.status_code == 400:
            print("⚠️ Requisição inválida (400) — verifique parâmetros.")
        else:
            print(f"⚠️ Erro {r.status_code}: {r.text}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
    print(f"⏱️ Finalizado em {time.time()-inicio:.2f}s")
    return False


def coletar_ligas_brasileiras():
    """Coleta as ligas do país Brasil e salva em CSV"""
    print("📡 Coletando ligas brasileiras...")
    url = f"{BASE_URL}/leagues/countries/{COUNTRY_ID}?api_token={TOKEN}"
    try:
        r = requests.get(url)
        if r.status_code != 200:
            print(f"⚠️ Erro {r.status_code}: {r.text}")
            return pd.DataFrame()

        data = r.json().get("data", [])
        if not data:
            print("⚠️ Nenhum dado retornado.")
            return pd.DataFrame()

        df = pd.DataFrame([
            {
                "id": l["id"],
                "nome": l["name"],
                "tipo": l.get("type"),
                "temporada_atual": l.get("currentseason", {}).get("id"),
                "ultima_atualizacao": l["updated_at"]
            }
            for l in data
        ])
        df["data_extracao"] = pd.Timestamp.now()
        df.sort_values("nome", inplace=True)
        df.to_csv("ligas_brasileiras.csv", index=False, encoding="utf-8-sig")
        print(f"💾 Arquivo salvo: ligas_brasileiras.csv ({len(df)} linhas)")
        return df
    except Exception as e:
        print(f"❌ Erro ao coletar ligas: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    print("\n🚀 Iniciando integração com Sportmonks...\n")
    if validar_token():
        coletar_ligas_brasileiras()
    print("\n✅ Processo finalizado.\n")
