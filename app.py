import streamlit as st
from utils import load_players, load_user_progress, save_user_progress, get_next_trio
import pandas as pd

USERS = {
    "Wendell": "458638", "Edu": "233472", "TTU": "190597", "Patrick": "471725",
    "Gian": "127917", "Behs": "955652", "Lorenzo": "824386", "Alessandro": "800506",
    "TX": "620075", "Ricardo": "484772", "Ed": "709678", "Raphael": "611310"
}

LABELS = ["", "Start", "Bench", "Drop"]
LABEL_EMOJIS = {"Start": "✅", "Bench": "🟨", "Drop": "❌", "": "⚪"}
LABEL_COLORS = {"Start": "#4CAF50", "Bench": "#FFC107", "Drop": "#F44336", "": "#CCCCCC"}

st.set_page_config(page_title="Fantasy Football Ranking App", layout="wide")
st.title("🏈 Fantasy Football Ranking App")

# Etapa 1: Seleção do usuário
if "user_selected" not in st.session_state:
    st.session_state.user_selected = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.user_selected:
    st.subheader("Escolha seu nome:")
    cols = st.columns(4)
    for i, name in enumerate(USERS):
        if cols[i % 4].button(name):
            st.session_state.user_selected = name
    st.stop()

# Etapa 2: Autenticação por senha (exceto Patrick)
if not st.session_state.authenticated:
    if st.session_state.user_selected == "Patrick":
        st.session_state.authenticated = True
    else:
        st.subheader(f"Olá, {st.session_state.user_selected}! Digite sua senha:")
        pwd = st.text_input("Senha (6 dígitos)", type="password")
        if st.button("Entrar"):
            if USERS[st.session_state.user_selected] == pwd:
                st.session_state.authenticated = True
                st.experimental_rerun()
            else:
                st.error("Senha incorreta.")
        st.stop()

# Etapa 3: Seleção da posição
user = st.session_state.user_selected
position = st.selectbox("Escolha a posição para ranquear:", ["QB", "RB", "WR", "TE"])
players_df = load_players(position)
all_players = players_df["PLAYER NAME"].tolist()

# Carregar progresso
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

# Próximo trio
remaining = [p for p in all_players if p not in progress["ranked"]]
trio = get_next_trio(remaining, progress["history"], progress["scores"])

# Inicializar ou atualizar as escolhas
if "choices" not in st.session_state or set(st.session_state.choices.keys()) != set(trio):
    st.session_state.choices = {p: "" for p in trio}

choices = st.session_state.choices

# Atualiza automaticamente o terceiro status se dois já foram definidos
used_statuses = [v for v in choices.values() if v]
if len(used_statuses) == 2:
    remaining_status = [s for s in ["Start", "Bench", "Drop"] if s not in used_statuses][0]
    for p in trio:
        if choices[p] == "":
            choices[p] = remaining_status

st.subheader("🟢 Clique no nome do jogador para rotacionar a escolha")

cols = st.columns(3)
for i, player in enumerate(trio):
    label = choices[player]
    emoji = LABEL_EMOJIS[label]
    color = LABEL_COLORS[label]

    with cols[i]:
        st.markdown(f"""
            <div style='text-align:center; font-size:20px; font-weight:bold;
                        color:{color}; margin-bottom:0.5em'>
                {emoji} {label if label else "Sem escolha"}
            </div>
        """, unsafe_allow_html=True)

        if st.button(player, key=f"btn_{player}"):
            current = choices[player]
            used = set(v for k, v in choices.items() if k != player)
            current_idx = LABELS.index(current)
            for offset in range(1, len(LABELS)):
                candidate = LABELS[(current_idx + offset) % len(LABELS)]
                if candidate == "" or candidate not in used:
                    choices[player] = candidate
                    # Se agora houver 2 definidos, já preenche o 3º
                    filled = [v for v in choices.values() if v]
                    if len(filled) == 2:
                        rem_status = [s for s in ["Start", "Bench", "Drop"] if s not in filled][0]
                        for pp in trio:
                            if choices[pp] == "":
                                choices[pp] = rem_status
                    break
            st.experimental_rerun()

# Confirmar se todos os status estão definidos
if set(choices.values()) == {"Start", "Bench", "Drop"}:
    if st.button("✅ Confirmar escolha e continuar"):
        for player, label in choices.items():
            score = {"Start": 3, "Bench": 2, "Drop": 1}[label]
            progress["scores"][player] = progress["scores"].get(player, 0) + score
            if player not in progress["ranked"]:
                progress["ranked"].append(player)
        progress["history"].append(tuple(sorted(trio)))
        save_user_progress(user, position, progress)
        del st.session_state.choices
        st.experimental_rerun()
