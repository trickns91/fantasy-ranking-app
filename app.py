import streamlit as st
import random
from utils import load_players, load_user_progress, save_user_progress, get_next_trio_heuristic, get_recent_players

st.set_page_config(page_title="Fantasy Ranking App", layout="centered")

usuarios = {
    "Patrick": "", "Wendell": "471725", "Edu": "903152", "TTU": "235817",
    "Gian": "582034", "Behs": "710394", "Lorenzo": "839124", "Alessandro": "294035",
    "TX": "918273", "Ricardo": "450192", "Ed": "384920", "Raphael": "672103"
}

st.title("🏈 Brain League Rankings")

# Etapa 1 - seleção de usuário
if "user" not in st.session_state:
    st.subheader("Escolha seu nome:")
    cols = st.columns(4)
    for i, name in enumerate(usuarios):
        if cols[i % 4].button(name):
            st.session_state["user"] = name
            st.session_state["authenticated"] = False
            st.rerun()
    st.stop()

# Etapa 2 - autenticação
user = st.session_state["user"]
if not st.session_state.get("authenticated", False):
    senha = st.text_input(f"Digite a senha para {user}:", type="password")
    if senha == usuarios[user]:
        st.session_state["authenticated"] = True
        st.rerun()
    else:
        st.stop()

# Etapa 3 - seleção de posição
st.subheader(f"Olá, {user}! Escolha a posição para ranquear:")
posicoes = ["QB", "RB", "WR", "TE"]
cols = st.columns(4)
for i, pos in enumerate(posicoes):
    if cols[i].button(pos):
        st.session_state["position"] = pos
        st.rerun()

if "position" not in st.session_state:
    st.stop()

position = st.session_state["position"]
all_players_df = load_players(position)
all_players = all_players_df["PLAYER NAME"].tolist()

# Etapa 4 - progresso do usuário
progress = load_user_progress(user, position)
recent_players = get_recent_players(progress["history"], max_recent=6)

tiers = all_players_df["TIERS"].tolist() if "TIERS" in all_players_df.columns else None
trio = get_next_trio_heuristic(all_players, progress["preferences"], progress["history"], k=3, tiers=tiers, exclude=recent_players)

st.markdown(f"### 🔢 Comparação - {position}")

if not trio:
    st.success("Todas as comparações necessárias foram feitas!")
    st.stop()

st.markdown("**Quem vale mais na Brain League, para você?**")

for player in trio:
    if st.button(player):
        outros = [p for p in trio if p != player]
        for p in outros:
            progress["preferences"].append([player, p])
            progress["history"].append(tuple(sorted([player, p])))
        save_user_progress(user, position, progress)
        st.rerun()

# Progresso
comparacoes = sum(1 for pair in progress["history"] if isinstance(pair, (list, tuple)) and len(pair) == 2)
total_necessarias = len(all_players) * 2
percentual = int(100 * comparacoes / total_necessarias)

st.write(f"Progresso: {percentual}% ({comparacoes} de {total_necessarias} comparações)")
st.button("🔍 Ver prévia do ranking")

# Reset ranking
with st.expander("🔁 Resetar ranking"):
    if st.button("Confirmar reset"):
        senha_reset = st.text_input(f"Digite sua senha para confirmar o reset de {position}:", type="password")
        if senha_reset == usuarios[user]:
            save_user_progress(user, position, {"preferences": [], "history": [], "ranked": []})
            st.success("Ranking resetado com sucesso!")
            st.rerun()
