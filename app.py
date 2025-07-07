import streamlit as st
from utils import load_players, save_user_ranking, compare_with_fantasypros
import pandas as pd

st.set_page_config(page_title="Fantasy Football Ranking App", layout="wide")

st.title("🏈 Fantasy Football Ranking App")
st.markdown("Crie seu ranking por posição — estilo **Start / Bench / Drop** — e compare com o FantasyPros!")

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

user_name = st.text_input("Digite seu nome para começar:", st.session_state.user_name)
if user_name:
    st.session_state.user_name = user_name
    st.success(f"Bem-vindo(a), {user_name}!")

    position = st.selectbox("Escolha a posição:", ["QB", "RB", "WR", "TE"])
    top_pct = st.radio("Quantos jogadores quer ranquear?", ["Top 50%", "Todos"])

    players_df = load_players(position)
    if top_pct == "Top 50%":
        players_df = players_df.head(len(players_df) // 2)

    st.markdown(f"### Ranqueie os jogadores de {position}")
    ranked_players = []
    pool = players_df["PLAYER NAME"].tolist()

    while len(pool) >= 3:
        options = pool[:3]
        st.subheader(f"Escolha entre:")
        choice = st.radio("Start / Bench / Drop", options, key=f"group_{len(ranked_players)}")
        ranked_players.append(choice)
        pool.remove(choice)
        pool = [p for p in pool if p not in options]

    if pool:
        ranked_players.extend(pool)

    if st.button("Finalizar Ranking"):
        df_result = pd.DataFrame({
            "PLAYER NAME": ranked_players,
            "RANK": list(range(1, len(ranked_players) + 1))
        })
        st.dataframe(df_result)
        save_user_ranking(user_name, position, df_result)

        # Comparar com FantasyPros
        comparison = compare_with_fantasypros(position, df_result)
        st.markdown("### 📊 Diferenças com o ranking original")
        st.dataframe(comparison)

        # Baixar como Excel
        st.download_button(
            label="📥 Baixar ranking em Excel",
            data=df_result.to_csv(index=False).encode("utf-8"),
            file_name=f"{user_name}_{position}_ranking.csv",
            mime="text/csv"
        )
