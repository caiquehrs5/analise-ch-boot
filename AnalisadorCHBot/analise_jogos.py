import requests


PI_URL = "https://v3.football.api-sports.io"

# IDs oficiais dos campeonatos
CAMPEONATOS = {
    "Brasileirão Série A": 71,
    "Premier League": 39,
    "La Liga": 140,
    "Champions League": 2,
    "Libertadores": 13
}

def listar_campeonatos():
    return list(CAMPEONATOS.keys())

def buscar_jogos(campeonato_nome):
    league_id = CAMPEONATOS.get(campeonato_nome)
    if not league_id:
        return f"⚠️ Campeonato '{campeonato_nome}' não encontrado."

    headers = {"x-apisports-key": API_KEY}
    params = {"league": league_id, "season": 2025, "next": 10}
    url = f"{API_URL}/fixtures"

    resposta = requests.get(url, headers=headers, params=params)
    if resposta.status_code != 200:
        return f"❌ Erro ao buscar dados ({resposta.status_code})"

    dados = resposta.json()
    jogos = dados.get("response", [])

    if not jogos:
        return "Nenhum jogo encontrado nos próximos dias."

    texto = f"📅 *Próximos jogos - {campeonato_nome}:*\n\n"
    for j in jogos:
        casa = j['teams']['home']['name']
        fora = j['teams']['away']['name']
        data = j['fixture']['date'].replace('T', ' ').split('+')[0]
        texto += f"⚽ {casa} x {fora}\n🕐 {data}\n\n"

    return texto
