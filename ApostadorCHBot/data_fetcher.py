import requests
import pandas as pd
import time

API_KEY = "0fb8f669a861bc861b75f6d00bb53b39"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

def check_league_availability():
    """Verifica se a Série A (ID 71) está disponível."""
    url = f"{BASE_URL}/leagues?id=71"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"⚠️ Erro {r.status_code}: {r.text}")
        return
    data = r.json()
    league = data["response"][0]["league"]["name"]
    country = data["response"][0]["country"]["name"]
    print(f"🏆 Liga disponível: {league} ({country})")

def fetch_brasileirao_2023():
    """Baixa todos os jogos da Série A 2023 via API-Football."""
    league_id = 71
    season = 2023
    url = f"{BASE_URL}/fixtures?league={league_id}&season={season}"
    print(f"📡 Coletando dados do Brasileirão Série A {season}...")

    r = requests.get(url, headers=HEADERS)
    if r.status_code == 429:
        print("⚠️ Limite de requisições atingido. Tente mais tarde.")
        return
    elif r.status_code == 402:
        print("🚫 Plano atual não permite acesso a essa temporada.")
        return
    elif r.status_code != 200:
        print(f"❌ Erro {r.status_code}: {r.text}")
        return

    matches = r.json().get("response", [])
    print(f"✅ {len(matches)} partidas encontradas.")

    rows = []
    for m in matches:
        f, l, t, g = m["fixture"], m["league"], m["teams"], m["goals"]
        rows.append({
            "data": f["date"][:10],
            "rodada": l.get("round"),
            "time_casa": t["home"]["name"],
            "time_fora": t["away"]["name"],
            "gols_casa": g["home"],
            "gols_fora": g["away"],
            "vencedor": (
                "Empate" if g["home"] == g["away"]
                else t["home"]["name"] if g["home"] > g["away"] else t["away"]["name"]
            ),
            "status": f["status"]["short"],
            "estadio": f["venue"]["name"] if f.get("venue") else None
        })

    df = pd.DataFrame(rows)
    df.sort_values("data", inplace=True)
    df.to_csv("historico_2023.csv", index=False, encoding="utf-8-sig")
    print(f"💾 Arquivo salvo: historico_2023.csv ({len(df)} linhas)")

if __name__ == "__main__":
    start = time.time()
    check_league_availability()
    fetch_brasileirao_2023()
    print(f"⏱️ Finalizado em {time.time()-start:.2f}s")
