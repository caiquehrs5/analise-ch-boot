# === CH FUTEBOL INSIGHTS BOT 9.0.2 ===
# Autor: Carlos Henrique (CH)
# Plataforma: Replit + Telegram
# IA adaptativa com confiabilidade dinâmica e fallback de imagem

import telebot
import requests
from io import BytesIO
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from datetime import datetime
import os
import re
from keep_alive import keep_alive

# === CONFIGURAÇÕES ===
keep_alive()
TOKEN = "8302402604:AAEOl2ibTxyIf5fFWbdn7WTJpCYqkMHYyYM"
bot = telebot.TeleBot(TOKEN)
HIST_FILE = "brasileirao_2025.csv"

# === FUNÇÕES BASE ===
def limpar_nome(time):
    return re.sub(r"[^A-Za-zÀ-ÿ0-9\s]", "", time).strip()

def carregar_historico():
    if os.path.exists(HIST_FILE):
        try:
            return pd.read_csv(HIST_FILE)
        except:
            return pd.DataFrame(columns=["time_casa","time_fora","gols_casa","gols_fora","resultado","data","hora"])
    else:
        return pd.DataFrame(columns=["time_casa","time_fora","gols_casa","gols_fora","resultado","data","hora"])

# === SCRAPING DA CBF ===
def atualizar_dados():
    print("📡 Coletando dados do Brasileirão Série A 2025...")
    url = "https://www.cbf.com.br/competicoes/brasileiro-serie-a/tabela"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    partidas = soup.select("li.item-jogo")
    registros = []

    for p in partidas:
        casa = p.select_one(".time.mandante")
        fora = p.select_one(".time.visitante")
        placar = p.select_one(".placar")
        data = p.select_one(".data")
        hora = p.select_one(".hora")

        if casa and fora:
            time_casa = limpar_nome(casa.text)
            time_fora = limpar_nome(fora.text)
            data_jogo = data.text.strip() if data else "A definir"
            hora_jogo = hora.text.strip() if hora else "-"
            if placar and "x" in placar.text:
                try:
                    gols = [int(x.strip()) for x in placar.text.split("x")]
                    resultado = "C" if gols[0] > gols[1] else ("F" if gols[1] > gols[0] else "E")
                except:
                    gols = [0, 0]
                    resultado = "E"
            else:
                gols = [0, 0]
                resultado = "E"
            registros.append([time_casa, time_fora, gols[0], gols[1], resultado, data_jogo, hora_jogo])

    if registros:
        df = pd.DataFrame(registros, columns=["time_casa","time_fora","gols_casa","gols_fora","resultado","data","hora"])
        df.to_csv(HIST_FILE, index=False)
        print(f"✅ {len(df)} jogos salvos em {HIST_FILE}")
        return f"✅ Base atualizada com {len(df)} partidas reais da CBF."
    else:
        return "⚠️ Nenhum jogo encontrado no momento. A CBF pode estar atualizando a tabela."

# === IA DE ANÁLISE ===
def gerar_analise(time_casa, time_fora):
    df = carregar_historico()
    if df.empty:
        return "⚠️ Nenhum dado disponível. Use /atualizar primeiro."

    df["y"] = df["resultado"].map({"C":0,"E":1,"F":2}).fillna(1).astype(int)
    X = df[["gols_casa","gols_fora"]].fillna(df[["gols_casa","gols_fora"]].mean())
    y = df["y"]

    model = LogisticRegression(max_iter=400)
    model.fit(X, y)
    print(f"[IA] Modelo treinado com {len(df)} partidas.")

    def media_gols(time, mandante=True):
        filtro = df[df["time_casa" if mandante else "time_fora"] == time]
        col = "gols_casa" if mandante else "gols_fora"
        return filtro[col].mean() if not filtro.empty else 1.0

    mc, mf = media_gols(time_casa, True), media_gols(time_fora, False)
    prob = model.predict_proba([[mc, mf]])[0]
    casa_pct, empate_pct, fora_pct = round(prob[0]*100,1), round(prob[1]*100,1), round(prob[2]*100,1)
    confiab = round(abs(casa_pct - fora_pct) * 0.5 + 50, 1)
    sugestao = "1 (Casa)" if casa_pct > fora_pct else ("2 (Fora)" if fora_pct > casa_pct else "X (Empate)")

    return (
        f"📊 *Análise - CH Futebol Insights 9.0.2*\n"
        f"🏠 {time_casa}: {casa_pct}%\n"
        f"⚖️ Empate: {empate_pct}%\n"
        f"🛫 {time_fora}: {fora_pct}%\n\n"
        f"💡 *Sugestão:* {sugestao}\n"
        f"🔒 *Confiabilidade:* {confiab}%\n\n"
        f"📈 *Média de gols (últimos jogos)*\n"
        f"▪️ {time_casa}: {mc:.1f}\n"
        f"▪️ {time_fora}: {mf:.1f}\n\n"
        f"📅 Base: {len(df)} partidas reais da CBF"
    )

# === COMANDOS TELEGRAM ===
@bot.message_handler(commands=["start","ajuda"])
def start_cmd(message):
    texto = (
        "👋 *Bem-vindo ao CH Futebol Insights Bot 9.0.2!*\n\n"
        "⚽ IA adaptativa para análise do *Brasileirão Série A 2025*.\n"
        "📊 Treinamento com dados reais da *CBF* e análise contextual de desempenho.\n\n"
        "📋 *Comandos disponíveis:*\n"
        "🔹 `/atualizar` → atualiza a base de dados CBF\n"
        "🔹 `/jogo TimeCasa x TimeFora` → gera análise estatística\n"
        "🔹 `/status` → mostra partidas registradas\n\n"
        "────────────────────────────\n"
        "🤝 Desenvolvido por *CH* – Futebol Insights ⚙️"
    )

    logo_path = "logo_brasileirao.png"
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as logo:
                bot.send_photo(message.chat.id, logo, caption=texto, parse_mode="Markdown")
        except:
            bot.send_message(message.chat.id, texto, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(commands=["status"])
def status_cmd(message):
    df = carregar_historico()
    bot.reply_to(message, f"📈 Base atual contém {len(df)} partidas registradas do Brasileirão Série A 2025.")

@bot.message_handler(commands=["atualizar"])
def atualizar_cmd(message):
    resultado = atualizar_dados()
    bot.reply_to(message, resultado)

@bot.message_handler(commands=["jogo"])
def jogo_cmd(message):
    try:
        padrao = re.compile(r"^/jogo\s+([\w\sÀ-ÿ]+)\s+x\s+([\w\sÀ-ÿ]+)$", re.IGNORECASE)
        match = padrao.match(message.text)
        if not match:
            bot.reply_to(message, "⚠️ Formato incorreto. Use `/jogo TimeCasa x TimeFora`.")
            return
        time_casa, time_fora = match.group(1).strip(), match.group(2).strip()
        analise = gerar_analise(time_casa, time_fora)
        bot.reply_to(message, analise, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro ao processar análise: {e}")

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.reply_to(message, "⚽ Use `/atualizar` para baixar dados ou `/jogo Palmeiras x Botafogo` para análise.")

# === EXECUÇÃO ===
print("🤖 CH Futebol Insights Bot 9.0.2 iniciado com IA adaptativa e scraping da CBF ⚽")
bot.polling()
