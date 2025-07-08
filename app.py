
import streamlit as st
import pandas as pd
import random
import networkx as nx
from collections import Counter
from utils import (
    load_players, load_user_progress, save_user_progress,
    get_next_trio_heuristic, get_recent_players
)

st.set_page_config(page_title="Fantasy Ranking App", layout="centered")

usuarios = {
    "Patrick": "", "Wendell": "471725", "Edu": "903152", "TTU": "235817",
    "Gian": "582034", "Behs": "710394", "Lorenzo": "839124", "Alessandro": "294035",
    "TX": "918273", "Ricardo": "450192", "Ed": "384920", "Raphael": "672103"
}

st.title("🏈 Brain League Rankings")

if "user" not in st.session_state:
    st.subheader("Escolha seu nome:")
    cols = st.columns(4)
    for i, name in enumerate(usuarios):
        if cols[i % 4].button(name):
            st.session_state["user"] = name
            st.session_state["authenticated"] = False
            st.session_state["pagina"] = "comparar"
            st.rerun()
    st.stop()

user = st.session_state["user"]
if not st.session_state.get("authenticated", False):
    senha = st.text_input(f"Digite a senha para {user}:", type="password")
    if senha == usuarios[user]:
        st.session_state["authenticated"] = True
        st.rerun()
    else:
        st.stop()

st.subheader(f"Olá, {user}! Escolha a posição:")
posicoes = ["QB", "RB", "WR", "TE"]
cols = st.columns(4)
for i, pos in enumerate(posicoes):
    if cols[i].button(pos):
        st.session_state["position"] = pos
        st.session_state["pagina"] = "comparar"
        st.rerun()

if "position" not in st.session_state:
    st.stop()

position = st.session_state["position"]
all_players_df = load_players(position)
all_players = all_players_df["PLAYER NAME"].tolist()
progress = load_user_progress(user, position)
recent_players = get_recent_players(progress["history"], max_recent=6)

comparacoes = len(set(tuple(sorted(pair)) for pair in progress["history"]))
total_necessarias = len(all_players) * 2
percentual = int(100 * comparacoes / total_necessarias)
st.markdown(f"### 📊 Progresso de {user} em {position}: {percentual}% ({comparacoes} de {total_necessarias})")

if st.button("🔍 Ver prévia do ranking"):
    st.session_state["pagina"] = "previa"
    st.rerun()

if st.session_state.get("pagina") == "previa":
    st.subheader("🔍 Prévia do Ranking")
    G = nx.DiGraph()
    for vencedor, perdedor in progress["preferences"]:
        G.add_edge(vencedor, perdedor)

    if nx.is_directed_acyclic_graph(G):
        ranking = list(nx.topological_sort(G))
    else:
        scores = {p: 0 for p in all_players}
        for vencedor, perdedor in progress["preferences"]:
            scores[vencedor] += 1
        ranking = sorted(scores, key=scores.get, reverse=True)

    if ranking:
        fantasypros_rank = {name: i for i, name in enumerate(all_players)}
        scores = {p: 0 for p in all_players}
        for vencedor, perdedor in progress["preferences"]:
            scores[vencedor] += 1

        sorted_players = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        tiers = []
        tier = []
        last_score = None
        for player, score in sorted_players:
            if last_score is None or abs(score - last_score) <= 1:
                tier.append((player, score))
            else:
                tiers.append(tier)
                tier = [(player, score)]
            last_score = score
        if tier:
            tiers.append(tier)

        for t_idx, t in enumerate(tiers):

        st.markdown(f"🎯 **Tier {t_idx+1}**")
        tier_data = []
        for nome, score in t:
            pos_fp = fantasypros_rank.get(nome, len(all_players))
            pos_user = ranking.index(nome)
            delta = pos_fp - pos_user
            tier_data.append({
                "Rank": pos_user + 1,
                "Jogador": nome,
                "Rank FP": pos_fp + 1,
                "Δ FP": delta
            })
        if tier_data:
            df_tier = pd.DataFrame(tier_data).sort_values("Rank").reset_index(drop=True)
            st.dataframe(df_tier, use_container_width=True)
st.stop()

# COMPARAÇÃO COM DROPDOWNS ESTÁVEIS
st.markdown("### 🧠 Para este trio, atribua uma escolha única a cada jogador:")

tiers = all_players_df["TIERS"].tolist() if "TIERS" in all_players_df.columns else None

if "trio_atual" not in st.session_state:
    st.session_state["trio_atual"] = get_next_trio_heuristic(
        all_players, progress["preferences"], progress["history"], k=3,
        tiers=tiers, exclude=recent_players
    )
trio = st.session_state["trio_atual"]

if not trio:
    st.success("Todas as comparações necessárias foram feitas!")
    st.stop()

options = ["", "Start", "Bench", "Drop"]
for player in trio:
    if f"escolha_{player}" not in st.session_state:
        st.session_state[f"escolha_{player}"] = ""

# Mostrar os jogadores em uma “tabela”
for player in trio:
    st.selectbox(
        f"{player}",
        options,
        index=options.index(st.session_state[f'escolha_{player}']),
        key=f"escolha_{player}"
    )

# Validação + botão
selected = [st.session_state[f"escolha_{p}"] for p in trio]
if st.button("✅ Confirmar escolhas"):
    if "" not in selected and len(set(selected)) == 3:
        start = [p for p in trio if st.session_state[f"escolha_{p}"] == "Start"][0]
        bench = [p for p in trio if st.session_state[f"escolha_{p}"] == "Bench"][0]
        drop = [p for p in trio if st.session_state[f"escolha_{p}"] == "Drop"][0]

        comparacoes = [
            [start, bench],
            [start, drop],
            [bench, drop]
        ]
        for c in comparacoes:
            if c not in progress["preferences"]:
                progress["preferences"].append(c)
            sorted_pair = tuple(sorted(c))
            if sorted_pair not in progress["history"]:
                progress["history"].append(sorted_pair)
        save_user_progress(user, position, progress)

        # Resetar trio e escolhas
        for p in trio:
            st.session_state.pop(f"escolha_{p}", None)
        st.session_state["trio_atual"] = get_next_trio_heuristic(
            all_players, progress["preferences"], progress["history"], k=3,
            tiers=tiers, exclude=get_recent_players(progress["history"], max_recent=6)
        )
        st.rerun()
    else:
        st.warning("Preencha uma opção diferente para cada jogador.")

# Reset
with st.expander("🔁 Resetar ranking"):
    senha_reset = st.text_input(f"Digite sua senha para confirmar o reset de {position}:", type="password")
    if st.button("Confirmar reset"):
        if senha_reset == usuarios[user]:
            save_user_progress(user, position, {"preferences": [], "history": [], "ranked": []})
            st.success("Ranking resetado com sucesso!")
            for k in list(st.session_state.keys()):
                if k.startswith("escolha_") or k == "trio_atual":
                    del st.session_state[k]
            st.rerun()
