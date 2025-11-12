from pathlib import Path
import pandas as pd
import re

CSV_PATH = Path(__file__).resolve().parent / "historico.csv"

def carregar_ods_brasileirao(caminho=CSV_PATH):
    """Carrega CSV local de partidas."""
    if not Path(caminho).exists():
        raise FileNotFoundError(
            f"Base '{caminho}' não encontrada. Gere o CSV com data_fetcher.py"
        )
    return pd.read_csv(caminho)

def analisar_partida_ods(time_casa, time_fora):
    df = carregar_ods_brasileirao()
    part = df[
        (df["time_casa"].str.lower() == time_casa.lower())
        & (df["time_fora"].str.lower() == time_fora.lower())
    ]

    if part.empty:
        return f"Não há confrontos recentes entre {time_casa} e {time_fora}!"

    vit_casa = len(part[part["resultado"] == "C"])
    empates = len(part[part["resultado"] == "E"])
    vit_fora = len(part[part["resultado"] == "F"])

    total = len(part)
    gols_casa = part["gols_casa"].sum()
    gols_fora = part["gols_fora"].sum()

    media_gols = (gols_casa + gols_fora) / total if total else 0
    ultimos_jogos = part.tail(5)

    resposta = f"Análise: {time_casa} x {time_fora}\n"
    resposta += f"Partidas recentes: {total}\n"
    resposta += f"Vitórias {time_casa}: {vit_casa} | Empates: {empates} | Vitórias {time_fora}: {vit_fora}\n"
    resposta += f"Gols totais: {gols_casa} x {gols_fora} (média {media_gols:.2f} gols/jogo)\n"
    resposta += "Últimos jogos:\n"
    for _, row in ultimos_jogos.iterrows():
        placar = f"{row['gols_casa']} x {row['gols_fora']}"
        vencedor = (
            time_casa if row["resultado"] == "C"
            else time_fora if row["resultado"] == "F"
            else "Empate"
        )
        resposta += f"  {row['time_casa']} {placar} {row['time_fora']} → {vencedor}\n"

    return resposta


def processar_mensagem(msg: str) -> str:
    """Intercepta comandos '/analisar' e chama análise do CSV."""
    texto = msg.strip()
    if not texto:
        return "Exemplo de uso: /analisar Corinthians x Vasco da Gama"

    texto_lower = texto.lower()
    for prefixo in ("/analisar", "analisar"):
        if texto_lower.startswith(prefixo):
            texto = texto[len(prefixo):].strip()
            texto_lower = texto.lower()
            break

    if not texto:
        return "Exemplo de uso: /analisar Corinthians x Vasco da Gama"

    partes = re.split(r"\s+x\s+", texto, maxsplit=1, flags=re.IGNORECASE)
    if len(partes) == 2:
        try:
            return analisar_partida_ods(partes[0].strip(), partes[1].strip())
        except FileNotFoundError as err:
            return str(err)

    return "Comando/processo não reconhecido. Tente /analisar TIME1 x TIME2."
