import streamlit as st
from utils import load_players, load_user_progress, save_user_progress, get_next_trio
import pandas as pd

USERS = {
    "Wendell": "458638",
    "Edu": "233472",
    "TTU": "190597",
    "Patrick": "471725",
    "Gian": "127917",
    "Behs": "955652",
    "Lorenzo": "824386",
    "Alessandro": "800506",
    "TX": "620075",
    "Ricardo": "484772",
    "Ed": "709678",
    "Raphael": "611310"
}

LABELS = ["Start", "Bench", "Drop"]

st.set_page_config(page_title="Fantasy Football Ranking App", layout="wide")
st.title("🏈 Fantasy Football Ranking App - Clicável")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    name = st.text_input("Seu nome").strip()
    pwd = st.text_input("Senha (6 dígitos)", type="password")
    if st.button("Entrar"):
        if name in USERS and USERS[name] == pwd:
            st.session_state.authenticated = True
            st.session_state.user = name
            st.success("Acesso liberado!")
        else:
            st.error("Nome ou senha incorretos.")
    st.stop()

user = st.session_state.user
position = st.selectbox("Escolha a posição para ranquear:", ["QB", "RB", "WR", "TE"])
players_df = load_players(position)
all_players = players_df["PLAYER NAME"].tolist()

if "progress" not in st.session_state:
    st.session_state.progress = load_user_progress(user, position) or {
        "scores": {},
        "history": [],
        "ranked": []
    }

progress = st.session_state.progress

if len(progress["ranked"]) >= len(all_players):
    st.success("Ranking completo!")
    final_rank = sorted(progress["scores"].items(), key=lambda x: -x[1])
    df_result = pd.DataFrame(final_rank, columns=["PLAYER NAME", "SCORE"])
    st.dataframe(df_result)
    st.download_button(
        "📥 Baixar ranking em CSV",
        data=df_result.to_csv(index=False).encode("utf-8"),
        file_name=f"{st.session_state.user}_{position}_ranking.csv",
        mime="text/csv"
    )
    st.stop()

remaining = [p for p in all_players if p not in progress["ranked"]]
trio = get_next_trio(remaining, progress["history"], progress["scores"])
st.subheader("Clique para ordenar: Start → Bench → Drop")

if "choices" not in st.session_state:
    st.session_state.choices = {}

def next_label(current, used):
    for label in LABELS:
        if label not in used:
            return label
    return None

cols = st.columns(3)
used_labels = set(st.session_state.choices.values())

for i, player in enumerate(trio):
    label = st.session_state.choices.get(player, "")
    with cols[i]:
        if st.button(f"{player}\n[{label}]" if label else player, key=player):
            if label:
                del st.session_state.choices[player]
            else:
                used = set(st.session_state.choices.values())
                next_lbl = next_label("", used)
                if next_lbl:
                    st.session_state.choices[player] = next_lbl
            st.experimental_rerun()

if set(st.session_state.choices.values()) == set(LABELS):
    if st.button("Confirmar este ranking"):
        for player, label in st.session_state.choices.items():
            score = {"Start": 3, "Bench": 2, "Drop": 1}[label]
            progress["scores"][player] = progress["scores"].get(player, 0) + score
            if player not in progress["ranked"]:
                progress["ranked"].append(player)
        progress["history"].append(tuple(sorted(trio)))
        save_user_progress(user, position, progress)
        del st.session_state.choices
        st.experimental_rerun()
