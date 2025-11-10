import pandas as pd

CSV_PATH = 'brasileirao_odds_2023.csv'

def carregar_ods_brasileirao(caminho=CSV_PATH):
    """Carrega CSV de partidas e odds."""
    return pd.read_csv(caminho)

def analisar_partida_ods(time_casa, time_fora):
    df = carregar_ods_brasileirao()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    part = df[(df['HomeTeam'].str.lower() == time_casa.lower()) & (df['AwayTeam'].str.lower() == time_fora.lower())]

    if part.empty:
        return f"Não há confrontos recentes entre {time_casa} e {time_fora}!"

    vit_casa = len(part[part['FTR'] == 'H'])
    empates = len(part[part['FTR'] == 'D'])
    vit_fora = len(part[part['FTR'] == 'A'])

    total = len(part)
    gols_casa = part['FTHG'].sum()
    gols_fora = part['FTAG'].sum()

    media_gols = (gols_casa + gols_fora) / total

    odds_casa = part['B365H'].mean()
    odds_empate = part['B365D'].mean()
    odds_fora = part['B365A'].mean()

    ultimos_jogos = part.sort_values(by='Date', ascending=False).head(5)

    resposta = f"Análise: {time_casa} x {time_fora}\n"
    resposta += f"Partidas recentes: {total}\n"
    resposta += f"Vitórias {time_casa}: {vit_casa} | Empates: {empates} | Vitórias {time_fora}: {vit_fora}\n"
    resposta += f"Gols totais: {gols_casa} x {gols_fora} (média {media_gols:.2f} gols/jogo)\n"
    resposta += f"Odds médias: Casa {odds_casa:.2f} | Empate {odds_empate:.2f} | Fora {odds_fora:.2f}\n"
    resposta += f"Últimos jogos:\n"
    for _, row in ultimos_jogos.iterrows():
        data = row['Date'].strftime('%d/%m/%Y')
        placar = f"{row['FTHG']} x {row['FTAG']}"
        odd_casa = row['B365H']
        odd_empate = row['B365D']
        odd_fora = row['B365A']
        resposta += f"  {data} - {placar} (Odds Casa: {odd_casa}, Empate: {odd_empate}, Fora: {odd_fora})\n"

    return resposta


def processar_mensagem(msg: str) -> str:
    """Intercepta comandos '/analisar' e chama análise do CSV."""
    if "analisar" in msg.lower():
        padrao = msg.replace("Analisar", "").strip()
        if " x " in padrao:
            times = padrao.split(" x ")
            if len(times) == 2:
                return analisar_partida_ods(times[0].strip(), times[1].strip())
        return "Exemplo de uso: /analisar Corinthians x Vasco da Gama"
    return "Comando/processo não reconhecido. Tente /analisar TIME1 x TIME2."
