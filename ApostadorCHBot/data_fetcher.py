import requests
import pandas as pd
import time

API_KEY = "0fb8f669a861bc861b75f6d00bb53b39"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}


def check_league_availability():
    """Verifica se a Série A (ID 71) está disponível. Caso não, tenta listar ligas brasileiras."""
    url = f"{BASE_URL}/leagues?id=71"
    print(f"🔗 Verificando liga pelo endpoint: {url}")
    r = requests.get(url, headers=HEADERS)
    print(f"📡 Status: {r.status_code}")

    if r.status_code != 200:
        print(f"⚠️ Erro {r.status_code}: {r.text}")
        return None

    data = r.json()
    if not data.get("response"):
        print("❌ Nenhum resultado retornado pela API para o ID 71.")
        print("🧭 Tentando listar ligas do país 'Brazil' como alternativa...\n")
        alt_url = f"{BASE_URL}/leagues?country=Brazil"
        r_alt = requests.get(alt_url, headers=HEADERS)
        if r_alt.status_code == 200:
            alt_data = r_alt.json()
            if alt_data.get("response"):
                for l in alt_data["response"]:
                    print(
                        f"🏆 {l['league']['name']} | ID: {l['league']['id']} | Temporada: {l['seasons'][-1]['year']}"
                    )
            else:
                print("⚠️ Nenhuma liga encontrada no país 'Brazil'.")
        else:
            print(f"⚠️ Erro alternativo {r_alt.status_code}: {r_alt.text}")
        return None

    league = data["response"][0]["league"]["name"]
    country = data["response"][0]["country"]["name"]
    print(f"✅ Liga disponível: {league} ({country})")
    return 71


def fetch_brasileirao_2023():
    """Baixa todos os jogos da Série A 2023 via API-Football."""
    league_id = 71
    season = 2023
    url = f"{BASE_URL}/fixtures?league={league_id}&season={season}"
    print(f"\n📡 Coletando dados do Brasileirão Série A {season}...")

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        return

    data = r.json()
    matches = data.get("response", [])
    if not matches:
        print("⚠️ Nenhum jogo retornado. Verifique o ID da liga ou o plano da API.")
        return

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
    df["fonte"] = "API-Football"
    df["data_extracao"] = pd.Timestamp.now()
    df.sort_values("data", inplace=True)
    df.to_csv("historico_2023.csv", index=False, encoding="utf-8-sig")
    print(f"💾 Arquivo salvo: historico_2023.csv ({len(df)} linhas)")


if __name__ == "__main__":
    start = time.time()
    print("\n🚀 Iniciando verificação e coleta de dados...\n")
    league = check_league_availability()
    if league:
        fetch_brasileirao_2023()
    print(f"\n⏱️ Finalizado em {time.time()-start:.2f}s")
