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

LABELS = ["", "Start", "Bench", "Drop"]
COLORS = {
    "": "gray",
    "Start": "green",
    "Bench": "orange",
    "Drop": "red"
}

st.set_page_config(page_title="Fantasy Football Ranking App", layout="wide")
st.title("🏈 Fantasy Football Ranking App")

if "user_selected" not in st.session_state:
    st.session_state.user_selected = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Etapa 1: seleção do usuário
if not st.session_state.user_selected:
    st.subheader("Escolha seu nome:")
    cols = st.columns(4)
    names = list(USERS.keys())
    for i, name in enumerate(names):
        if cols[i % 4].button(name):
            st.session_state.user_selected = name
    st.stop()

# Etapa 2: autenticação
if not st.session_state.authenticated:
    st.subheader(f"Olá, {st.session_state.user_selected}! Digite sua senha:")
    pwd = st.text_input("Senha (6 dígitos)", type="password")
    if st.button("Entrar"):
        if USERS[st.session_state.user_selected] == pwd:
            st.session_state.authenticated = True
            st.success("Acesso liberado!")
        else:
            st.error("Senha incorreta.")
    st.stop()

user = st.session_state.user_selected
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
        file_name=f"{user}_{position}_ranking.csv",
        mime="text/csv"
    )
    st.stop()

# Gerar trio inteligente
remaining = [p for p in all_players if p not in progress["ranked"]]
trio = get_next_trio(remaining, progress["history"], progress["scores"])

if "choices" not in st.session_state:
    st.session_state.choices = {p: "" for p in trio}

st.subheader("Clique no botão de cada jogador para rotacionar: Start → Bench → Drop → Limpar")

cols = st.columns(3)
for i, player in enumerate(trio):
    current = st.session_state.choices.get(player, "")
    label = current if current else "Clique"
    color = COLORS[current]
    if cols[i].button(f"{player}\n[{label}]", key=player):
        used = set(st.session_state.choices.values())
        current_idx = LABELS.index(current)
        next_idx = (current_idx + 1) % len(LABELS)
        # Procurar próximo label disponível
        for offset in range(1, len(LABELS)):
            candidate = LABELS[(current_idx + offset) % len(LABELS)]
            if candidate == "" or candidate not in used:
                st.session_state.choices[player] = candidate
                break
        st.experimental_rerun()

if set(st.session_state.choices.values()) == {"Start", "Bench", "Drop"}:
    if st.button("Confirmar escolha"):
        for player, label in st.session_state.choices.items():
            score = {"Start": 3, "Bench": 2, "Drop": 1}[label]
            progress["scores"][player] = progress["scores"].get(player, 0) + score
            if player not in progress["ranked"]:
                progress["ranked"].append(player)
        progress["history"].append(tuple(sorted(trio)))
        save_user_progress(user, position, progress)
        del st.session_state.choices
        st.experimental_rerun()
