import streamlit as st
import pandas as pd
import os
from utils import load_players, load_user_progress, save_user_progress, get_next_trio_heuristic

st.set_page_config(page_title="Fantasy Ranking App", layout="centered")

st.title("Brain League Rankings")

# Lista fixa de usuários e senhas
usuarios = {
    "Patrick": "",
    "Wendell": "471725",
    "Edu": "830416",
    "TTU": "617239",
    "Gian": "952380",
    "Behs": "314067",
    "Lorenzo": "780392",
    "Alessandro": "104785",
    "TX": "569014",
    "Ricardo": "209873",
    "Ed": "398524",
    "Raphael": "845730"
}

positions = ["QB", "RB", "WR", "TE"]

# Seleção de usuário
st.subheader("Quem é você?")
cols = st.columns(4)
selected_user = None
for i, name in enumerate(usuarios):
    if cols[i % 4].button(name):
        st.session_state["user"] = name
        st.session_state["authenticated"] = False
        st.experimental_rerun()

# Autenticação
if "user" in st.session_state:
    user = st.session_state["user"]
    if not st.session_state.get("authenticated"):
        senha = st.text_input(f"Digite a senha para {user}:", type="password")
        if senha == usuarios[user]:
            st.session_state["authenticated"] = True
            st.experimental_rerun()
        else:
            st.stop()

# Posição
if "position" not in st.session_state:
    st.session_state["position"] = "QB"

st.subheader("Escolha a posição:")
cols = st.columns(len(positions))
for i, pos in enumerate(positions):
    if pos == st.session_state["position"]:
        cols[i].button(pos, disabled=True)
    else:
        if cols[i].button(pos):
            st.session_state["position"] = pos
            st.experimental_rerun()

position = st.session_state["position"]
user = st.session_state["user"]

players_df = load_players(position)
all_players = players_df["PLAYER NAME"].tolist()

progress = load_user_progress(user, position)

# Reset
with st.expander("⚙️ Resetar ranking", expanded=False):
    confirmar = st.checkbox(f"Tem certeza que quer zerar todas info de ranking de {position}?")
    senha_reset = st.text_input("Digite sua senha para confirmar:", type="password")
    if confirmar and senha_reset == usuarios[user]:
        progress = {"preferences": [], "history": [], "ranked": []}
        save_user_progress(user, position, progress)
        st.success("Ranking resetado com sucesso.")
        st.stop()

# Ranking finalizado?
if len(progress.get("ranked", [])) >= len(all_players):
    st.success("Ranking completo!")
    st.write("Resultado final:")
    st.write(progress["ranked"])
    st.stop()

# Pergunta
tiers = players_df.set_index("PLAYER NAME")["TIERS"].to_dict()
trio = get_next_trio_heuristic(all_players, progress["preferences"], progress["history"], k=3, tiers=tiers)

if not trio:
    st.info("Não há mais combinações únicas para exibir.")
    st.stop()

st.subheader("Quem vale mais na Brain League, para você?")
for player in trio:
    if st.button(player):
        outros = [p for p in trio if p != player]
        for outro in outros:
            progress["preferences"].append((player, outro))
            progress["history"].append(tuple(sorted((player, outro))))
        save_user_progress(user, position, progress)
        st.experimental_rerun()

st.write(f"Progresso: {len(progress['history'])} comparações feitas")
