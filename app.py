import streamlit as st
import random
import networkx as nx
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
            st.session_state["pagina"] = "comparar"
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
        st.session_state["pagina"] = "comparar"
        st.rerun()

if "position" not in st.session_state:
    st.stop()

position = st.session_state["position"]
all_players_df = load_players(position)
all_players = all_players_df["PLAYER NAME"].tolist()

# Etapa 4 - progresso do usuário
progress = load_user_progress(user, position)
recent_players = get_recent_players(progress["history"], max_recent=6)

# Progresso
comparacoes = len(set(tuple(sorted(pair)) for pair in progress["history"] if isinstance(pair, (list, tuple)) and len(pair) == 2))
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

        # Agrupar em tiers simples: 1 ponto de diferença = mesmo tier
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
            st.markdown(f"#### 🎯 Tier {t_idx+1}")
            st.write("""| Rank | Jogador | Δ FP | Score |
|------|---------|------|-------|""")
            for idx, (nome, score) in enumerate(t):
                delta = fantasypros_rank.get(nome, len(all_players)) - ranking.index(nome)
                emoji = "" if abs(delta) < 1 else ("🔺" if delta > 0 else "🔻")
                st.write(f"| {ranking.index(nome)+1} | {nome} | {delta:+} {emoji} | ⭐ {score} |")

    else:
        st.info("Ainda não há comparações suficientes para gerar ranking.")

    import pandas as pd

        if st.button("⬇️ Baixar ranking em CSV"):
            df_export = pd.DataFrame(ranking, columns=["PLAYER NAME"])
            df_export["Rank"] = df_export.index + 1
            df_export = df_export.merge(all_players_df, on="PLAYER NAME", how="left")
            st.download_button("📥 Download do Ranking", df_export.to_csv(index=False).encode('utf-8'), file_name=f"ranking_{user}_{position}.csv", mime="text/csv")
"📥 Download do Ranking", df_export.to_csv(index=False).encode('utf-8'), file_name=f"ranking_{user}_{position}.csv", mime="text/csv")

                if st.button("⬅️ Voltar para comparações"):
            st.session_state["pagina"] = "comparar"
        st.rerun()
    st.stop()

# Comparação
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
            if tuple(sorted([player, p])) not in progress["history"]:
                progress["history"].append(tuple(sorted([player, p])))
        save_user_progress(user, position, progress)
        st.rerun()

# Reset ranking
with st.expander("🔁 Resetar ranking"):
    if st.button("Confirmar reset"):
        senha_reset = st.text_input(f"Digite sua senha para confirmar o reset de {position}:", type="password")
        if senha_reset == usuarios[user]:
            save_user_progress(user, position, {"preferences": [], "history": [], "ranked": []})
            st.success("Ranking resetado com sucesso!")
            st.rerun()
