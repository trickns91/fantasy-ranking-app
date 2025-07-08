import streamlit as st
import pandas as pd
import random
import os
import json
import math

DATA_DIR = "data"
USER_DIR = "user_data"

def load_players(position):
    filepath = os.path.join(DATA_DIR, f"{position}.csv")
    df = pd.read_csv(filepath)
    return df

def load_user_progress(user, position):
    os.makedirs(USER_DIR, exist_ok=True)
    filepath = os.path.join(USER_DIR, f"{user}_{position}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    else:
        return {"votes": [], "history": []}

def save_user_progress(user, position, progress):
    os.makedirs(USER_DIR, exist_ok=True)
    filepath = os.path.join(USER_DIR, f"{user}_{position}.json")
    with open(filepath, "w") as f:
        json.dump(progress, f)

st.set_page_config(page_title="BL Trade Value", layout="centered")

usuarios = {
    "Patrick": "", "Wendell": "471725", "Edu": "903152", "TTU": "235817",
    "Gian": "582034", "Behs": "710394", "Lorenzo": "839124", "Alessandro": "294035",
    "TX": "918273", "Ricardo": "450192", "Ed": "384920", "Raphael": "672103"
}

st.title("💰 Valor de Trade - Brain League")

if "user" not in st.session_state:
    st.subheader("Escolha seu nome:")
    cols = st.columns(4)
    for i, name in enumerate(usuarios):
        if cols[i % 4].button(name):
            st.session_state["user"] = name
            st.rerun()
    st.stop()

user = st.session_state["user"]

if "position" not in st.session_state:
    st.subheader("Escolha a posição:")
    for pos in ["QB", "RB", "WR", "TE"]:
        if st.button(pos):
            st.session_state["position"] = pos
            st.rerun()
    st.stop()

position = st.session_state["position"]
players_df = load_players(position)
all_players = players_df.to_dict("records")
progress = load_user_progress(user, position)

total_jogadores = len(players_df)
pares_totais = total_jogadores * (total_jogadores - 1) // 2
pares_minimos = int(total_jogadores * math.log2(total_jogadores))
perguntas_minimas = pares_minimos // 2
perguntas_feitas = len(progress["votes"])
perguntas_restantes = max(0, perguntas_minimas - perguntas_feitas)

st.info(f"📊 Jogadores: {total_jogadores}  |  Perguntas mínimas: {perguntas_minimas}  |  Já respondidas: {perguntas_feitas}  |  Faltam: {perguntas_restantes}")

if st.button("🗑️ Resetar meu ranking"):
    progress = {"votes": [], "history": []}
    save_user_progress(user, position, progress)
    st.rerun()


# Remover jogadores já escolhidos para variar
recent = progress["history"][-9:] if progress["history"] else []
candidates = [p for p in all_players if p["PLAYER NAME"] not in recent]

if len(candidates) < 3:
    candidates = all_players

trio = random.sample(candidates, 3)

st.subheader("Qual o jogador mais valioso em uma trade da BL?")
cols = st.columns(3)
for i, jogador in enumerate(trio):
    nome = jogador["PLAYER NAME"]
    salario = jogador["SALARY_M"]
    with cols[i]:
        if st.button(f"{nome} (${salario}M)", key=f"btn_{i}"):
            progress["votes"].append(nome)
            progress["history"].append(nome)
            save_user_progress(user, position, progress)
            st.rerun()

# Mostrar total de votos
if st.button("📊 Ver ranking parcial"):
    st.subheader("Ranking Parcial")
    if progress["votes"]:
        contagem = pd.Series(progress["votes"]).value_counts()
        ranking = pd.DataFrame({"PLAYER NAME": contagem.index, "VOTOS": contagem.values})
        ranking = ranking.merge(players_df, on="PLAYER NAME", how="left")
        st.dataframe(ranking.sort_values("VOTOS", ascending=False).reset_index(drop=True))
        csv = ranking.to_csv(index=False)
        st.download_button("⬇️ Baixar ranking CSV", data=csv, file_name=f"{user}_{position}_ranking.csv", mime="text/csv")
    else:
        st.info("Você ainda não respondeu nenhuma pergunta.")
    st.subheader("Ranking Parcial")
    contagem = pd.Series(progress["votes"]).value_counts()
    ranking = pd.DataFrame({"PLAYER NAME": contagem.index, "VOTOS": contagem.values})
    ranking = ranking.merge(players_df, on="PLAYER NAME", how="left")
    st.dataframe(ranking.sort_values("VOTOS", ascending=False).reset_index(drop=True))

    csv = ranking.to_csv(index=False)
    st.download_button("⬇️ Baixar ranking CSV", data=csv, file_name=f"{user}_{position}_ranking.csv", mime="text/csv")