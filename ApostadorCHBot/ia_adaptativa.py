import pandas as pd

def carregar_dados(caminho="historico_2023.csv"):
    """Carrega e pré-processa os dados do Brasileirão 2023."""
    df = pd.read_csv(caminho)
    df["data"] = pd.to_datetime(df["data"])
    df.dropna(subset=["time_casa", "time_fora"], inplace=True)
    return df

def calcular_estatisticas(df):
    """Calcula estatísticas acumuladas e médias por time."""
    times = sorted(set(df["time_casa"]).union(df["time_fora"]))
    stats = []

    for time in times:
        jogos_casa = df[df["time_casa"] == time]
        jogos_fora = df[df["time_fora"] == time]

        gols_feitos = jogos_casa["gols_casa"].sum() + jogos_fora["gols_fora"].sum()
        gols_sofridos = jogos_casa["gols_fora"].sum() + jogos_fora["gols_casa"].sum()

        vitorias = len(df[df["vencedor"] == time])
        empates = len(df[df["vencedor"] == "Empate"])
        derrotas = len(df[(df["time_casa"] == time) | (df["time_fora"] == time)]) - vitorias - empates

        aproveitamento = round((vitorias * 3 + empates) / ((vitorias + empates + derrotas) * 3) * 100, 2)

        stats.append({
            "time": time,
            "jogos": vitorias + empates + derrotas,
            "vitorias": vitorias,
            "empates": empates,
            "derrotas": derrotas,
            "gols_feitos": gols_feitos,
            "gols_sofridos": gols_sofridos,
            "saldo": gols_feitos - gols_sofridos,
            "aproveitamento": aproveitamento
        })

    return pd.DataFrame(stats).sort_values(by="aproveitamento", ascending=False)

def analisar_partida(df, time_casa, time_fora):
    """Gera análise adaptativa de um confronto com base na temporada 2023."""
    base = calcular_estatisticas(df)
    c = base[base["time"] == time_casa].iloc[0]
    f = base[base["time"] == time_fora].iloc[0]

    prob_casa = 0.5 + (c["aproveitamento"] - f["aproveitamento"]) / 200
    prob_fora = 1 - prob_casa
    empate = 0.2 * (1 - abs(prob_casa - prob_fora))

    prob_casa = round(prob_casa - empate / 2, 2)
    prob_fora = round(prob_fora - empate / 2, 2)
    empate = round(empate, 2)

    return {
        "time_casa": time_casa,
        "time_fora": time_fora,
        "probabilidades": {
            "vitória_casa": prob_casa,
            "empate": empate,
            "vitória_fora": prob_fora
        },
        "dif_aproveitamento": round(c["aproveitamento"] - f["aproveitamento"], 2)
    }

if __name__ == "__main__":
    df = carregar_dados()
    resultado = analisar_partida(df, "Corinthians", "Vasco da Gama")
    print(resultado)
