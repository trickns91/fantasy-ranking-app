import streamlit as st
import random
import networkx as nx
import pandas as pd
from utils import (
    load_players, load_user_progress, save_user_progress,
    get_next_trio_heuristic, get_recent_players
)

st.set_page_config(page_title="Fantasy Ranking App", layout="centered")

# Usuários e senhas
usuarios = {
    "Patrick": "", "Wendell": "471725", "Edu": "903152", "TTU": "235817",
    "Gian": "582034", "Behs": "710394", "Lorenzo": "839124", "Alessandro": "294035",
    "TX": "918273", "Ricardo": "450192", "Ed": "384920", "Raphael": "672103"
}

st.title("🏈 Brain League Rankings")

# === Etapa 1: Seleção de usuário ===
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

# === Etapa 2: Autenticação ===
if not st.session_state.get("authenticated", False):
    senha = st.text_input(f"Digite a senha para {user}:", type="password")
    if senha == usuarios[user]:
        st.session_state["authenticated"] = True
        st.rerun()
    else:
        st.stop()

# === Etapa 3: Escolha da posição ===
st.subheader(f"Olá, {user}! Escolha a posição para ranquear:")
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

# === Etapa 4: Carregamento de progresso ===
progress = load_user_progress(user, position)
recent_players = get_recent_players(progress["history"], max_recent=6)

# === Progresso ===
comparacoes = len(set(tuple(sorted(pair)) for pair in progress["history"] if len(pair) == 2))
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
        for vencedor, _ in progress["preferences"]:
            scores[vencedor] += 1
        ranking = sorted(scores, key=scores.get, reverse=True)

    if ranking:
        fantasypros_rank = {name: i for i, name in enumerate(all_players)}
        scores = {p: 0 for p in all_players}
        for vencedor, _ in progress["preferences"]:
            scores[vencedor] += 1

        # Tiers por diferença de score
        sorted_players = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        tier_map = {}
        current_tier = 1
        last_score = None
        tiered = []
        for player, score in sorted_players:
            if last_score is None or abs(score - last_score) <= 1:
                pass
            else:
                current_tier += 1
            tier_map[player] = current_tier
            tiered.append((player, current_tier))
            last_score = score

        # Blocos por Tier
        st.markdown("## 📦 Jogadores por Tier")
        for tier_num in sorted(set(t for _, t in tiered)):
            st.markdown(f"### 🎯 Tier {tier_num}")
            st.write("| Rank | Jogador | Δ FP |")
            st.write("|------|---------|------|")
            for player, tier in tiered:
                if tier != tier_num:
                    continue
                rank = ranking.index(player) + 1
                delta = fantasypros_rank.get(player, len(all_players)) - rank
                emoji = "" if abs(delta) < 1 else ("🔺" if delta > 0 else "🔻")
                st.write(f"| {rank} | {player} | {delta:+} {emoji} |")

        # Exportar CSV ainda pode ser útil
        if st.button("⬇️ Baixar ranking em CSV"):
            df_export = pd.DataFrame(ranking, columns=["PLAYER NAME"])
            df_export["Rank"] = df_export.index + 1
            df_export["Tier"] = df_export["PLAYER NAME"].map(tier_map)
            df_export = df_export.merge(all_players_df, on="PLAYER NAME", how="left")
            st.download_button("📥 Download do Ranking", df_export.to_csv(index=False).encode('utf-8'),
                               file_name=f"ranking_{user}_{position}.csv", mime="text/csv")

    else:
        st.info("Ainda não há comparações suficientes para gerar ranking.")

    if st.button("⬅️ Voltar para comparações"):
        st.session_state["pagina"] = "comparar"
        st.rerun()

    st.stop()

# === Página de comparações ===
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
            if [player, p] not in progress["preferences"]:
                progress["preferences"].append([player, p])
            sorted_pair = tuple(sorted([player, p]))
            if sorted_pair not in progress["history"]:
                progress["history"].append(sorted_pair)
        save_user_progress(user, position, progress)
        st.rerun()

# === Reset ===
with st.expander("🔁 Resetar ranking"):
    senha_reset = st.text_input(f"Digite sua senha para confirmar o reset de {position}:", type="password")
    if st.button("Confirmar reset"):
        if senha_reset == usuarios[user]:
            save_user_progress(user, position, {"preferences": [], "history": [], "ranked": []})
            st.success("Ranking resetado com sucesso!")
            st.rerun()
