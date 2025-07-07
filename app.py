import streamlit as st
from utils import load_players, load_user_progress, save_user_progress, get_next_trio_heuristic
import pandas as pd
import networkx as nx
import os
import json
from math import comb
from collections import Counter

USERS = {
    "Wendell": "458638", "Edu": "233472", "TTU": "190597", "Patrick": "471725",
    "Gian": "127917", "Behs": "955652", "Lorenzo": "824386", "Alessandro": "800506",
    "TX": "620075", "Ricardo": "484772", "Ed": "709678", "Raphael": "611310"
}

st.set_page_config(page_title="Fantasy Football Ranking App", layout="wide")
st.title("🏈 Fantasy Football Ranking App")

if "user_selected" not in st.session_state:
    st.session_state.user_selected = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "confirm_reset" not in st.session_state:
    st.session_state.confirm_reset = False

if not st.session_state.user_selected:
    st.subheader("Escolha seu nome:")
    cols = st.columns(4)
    for i, name in enumerate(USERS):
        if cols[i % 4].button(name):
            st.session_state.user_selected = name
            st.session_state.confirm_reset = False
            st.stop()
    st.stop()

if not st.session_state.authenticated:
    st.subheader(f"Olá, {st.session_state.user_selected}! Digite sua senha:")
    pwd = st.text_input("Senha (6 dígitos)", type="password")
    if st.button("Entrar"):
        if USERS[st.session_state.user_selected] == pwd or st.session_state.user_selected == "Patrick":
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Senha incorreta.")


user = st.session_state.user_selected
position = st.selectbox("Escolha a posição para ranquear:", ["QB", "RB", "WR", "TE"])
players_df = load_players(position)
all_players = players_df["PLAYER NAME"].tolist()

# Recarrega sempre o progresso mais recente do disco
progress = load_user_progress(user, position) or {
    "preferences": [],
    "ranked": [],
    "history": []
}
st.session_state.progress = progress

# Botões de reset e pular
col1, col2 = st.columns(2)
if col1.button("🔁 Resetar ranking"):
    st.session_state.confirm_reset = True

if st.session_state.confirm_reset:
    with st.form(key="reset_form"):
        st.warning(f"Tem certeza que quer zerar todas as informações de ranking de {position}?")
        senha_confirma = st.text_input("Confirme sua senha para resetar:", type="password")
        submit = st.form_submit_button("Confirmar reset")
        if submit:
            if USERS[user] == senha_confirma:
                path = f"progress/{user}_{position}.json"
                if os.path.exists(path):
                    os.remove(path)
                st.session_state.progress = {
                    "preferences": [],
                    "ranked": [],
                    "history": []
                }
                st.session_state.confirm_reset = False
                st.success("Ranking reiniciado com sucesso. Recarregue a página ou selecione novamente a posição.")
                st.stop()
            else:
                st.error("Senha incorreta para confirmação.")

if col2.button("⏭️ Pular grupo"):
    progress["history"].append(tuple(sorted(get_next_trio_heuristic(all_players, progress["preferences"], progress["history"], k=4))))
    save_user_progress(user, position, progress)
    st.experimental_rerun()

if len(progress["ranked"]) >= len(all_players):
    st.success("Ranking completo!")
    G = nx.DiGraph()
    G.add_nodes_from(all_players)
    G.add_edges_from(progress["preferences"])
    ranking = list(nx.topological_sort(G))
    df_result = pd.DataFrame(ranking, columns=["PLAYER NAME"])
    df_result["RANK"] = range(1, len(df_result) + 1)
    st.dataframe(df_result)
    st.download_button(
        "📥 Baixar ranking em CSV",
        data=df_result.to_csv(index=False).encode("utf-8"),
        file_name=f"{user}_{position}_ranking.csv",
        mime="text/csv"
    )
    st.stop()

remaining = [p for p in all_players if p not in progress["ranked"]]
grupo = get_next_trio_heuristic(remaining, progress["preferences"], progress["history"], k=4)

st.subheader("Quem vale mais na Brain League, para você?")

cols = st.columns(4)
selected = None
for i, player in enumerate(grupo):
    with cols[i]:
        if st.button(player):
            selected = player
            break

if selected:
    others = [p for p in grupo if p != selected]
    for other in others:
        if (selected, other) not in progress["preferences"]:
            progress["preferences"].append((selected, other))

    progress["history"].append(tuple(sorted(grupo)))
    save_user_progress(user, position, progress)
    st.experimental_rerun()

# Exibir progresso
num_total_trios = comb(len(all_players), 2)
num_coletados = len(progress["preferences"])
pct = num_coletados / num_total_trios * 100
st.progress(min(pct / 100, 1.0))
st.caption(f"{num_coletados} comparações feitas de {num_total_trios} possíveis (~{pct:.1f}%)")
