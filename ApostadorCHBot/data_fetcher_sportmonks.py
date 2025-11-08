# -*- coding: utf-8 -*-
import requests
import pandas as pd
import os
import time

TOKEN = "IrTQK9UlTuwS5goNh6zQruXlpZTxcUtM11RoPwsd31Y26e9x2e73oufBS5HC"
BASE_URL = "https://api.sportmonks.com/v3/football"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def validar_token():
    print("🔍 Validando token...")
    url = f"{BASE_URL}/leagues"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        print("✅ Token válido – acesso confirmado.")
        return True
    else:
        print(f"❌ Erro {r.status_code}: {r.text}")
        return False

def coletar_temporada(ano):
    print(f"\n⚽ Coletando Série A {ano}...")
    url = f"{BASE_URL}/fixtures/seasons/{ano}?include=participants;venue"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"⚠️ Erro {r.status_code}: {r.text}")
        return pd.DataFrame()
    data = r.json().get("data", [])
    if not data:
        print("⚠️ Nenhum dado retornado para esta temporada.")
        return pd.DataFrame()

    rows = []
    for match in data:
        home, away = None, None
        if match.get("participants"):
            for p in match["participants"]:
                if p.get("meta", {}).get("location") == "home":
                    home = p.get("name")
                elif p.get("meta", {}).get("location") == "away":
                    away = p.get("name")
        venue = match.get("venue", {}).get("name") if match.get("venue") else None
        gols_home = match.get("home_score")
        gols_away = match.get("away_score")
        vencedor = "Empate"
        if isinstance(gols_home, int) and isinstance(gols_away, int):
            if gols_home > gols_away:
                vencedor = home
            elif gols_away > gols_home:
                vencedor = away
        rows.append({
            "data": match.get("starting_at", "")[:10],
            "temporada": ano,
            "time_casa": home,
            "time_fora": away,
            "gols_casa": gols_home,
            "gols_fora": gols_away,
            "vencedor": vencedor,
            "status": match.get("state", ""),
            "estadio": venue
        })
    return pd.DataFrame(rows)

def main():
    inicio = time.time()
    if not validar_token():
        return
    os.makedirs("dados", exist_ok=True)
    dfs = []
    for ano in [2023, 2024, 2025]:
        df_temp = coletar_temporada(ano)
        if not df_temp.empty:
            dfs.append(df_temp)
    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)
        path = "dados/historico_sportmonks.csv"
        df_final.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"\n💾 Arquivo consolidado: {path} ({len(df_final)} linhas)")
    else:
        print("⚠️ Nenhum dado salvo.")
    print(f"⏱️ Execução total: {time.time()-inicio:.2f}s")

if __name__ == "__main__":
    main()
