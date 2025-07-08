
import streamlit as st
import pandas as pd
import random
import networkx as nx
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

# Página de prévia do ranking
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
            st.markdown(f"##### 🎯 Tier {t_idx+1}")
            df_tier = pd.DataFrame([
                {
                    "Rank": ranking.index(nome)+1,
                    "Jogador": nome,
                    "Δ FP": fantasypros_rank.get(nome, len(all_players)) - ranking.index(nome)
                }
                for nome, score in t if nome in ranking
            ])
            st.table(df_tier.sort_values("Rank"))

        if st.button("📥 Baixar ranking em CSV"):
            df_export = pd.DataFrame(ranking, columns=["PLAYER NAME"])
            df_export["Rank"] = df_export.index + 1
            df_export = df_export.merge(all_players_df, on="PLAYER NAME", how="left")
            st.download_button("📥 Download do Ranking", df_export.to_csv(index=False).encode("utf-8"), file_name=f"ranking_{user}_{position}.csv", mime="text/csv")

    else:
        st.info("Ainda não há comparações suficientes para gerar ranking.")

    if st.button("⬅️ Voltar para comparações"):
        st.session_state["pagina"] = "comparar"
        st.rerun()

    st.stop()

# Comparação com 2 cliques (start, bench, drop)
st.markdown("### 🧠 Escolha: Start, Bench, Drop")
tiers = all_players_df["TIERS"].tolist() if "TIERS" in all_players_df.columns else None
trio = get_next_trio_heuristic(all_players, progress["preferences"], progress["history"], k=3, tiers=tiers, exclude=recent_players)

if not trio:
    st.success("Todas as comparações necessárias foram feitas!")
    st.stop()

random.shuffle(trio)
start = st.selectbox("🏈 Start:", trio, key="start")
bench_options = [p for p in trio if p != start]
bench = st.selectbox("🪑 Bench:", bench_options, key="bench")

if start and bench:
    drop = [p for p in trio if p not in [start, bench]][0]
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
    st.rerun()

# Reset ranking
with st.expander("🔁 Resetar ranking"):
    senha_reset = st.text_input(f"Digite sua senha para confirmar o reset de {position}:", type="password")
    if st.button("Confirmar reset"):
        if senha_reset == usuarios[user]:
            save_user_progress(user, position, {"preferences": [], "history": [], "ranked": []})
            st.success("Ranking resetado com sucesso!")
            st.rerun()
