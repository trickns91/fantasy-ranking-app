if "pagina" not in st.session_state:
    st.session_state["pagina"] = "comparar"

pagina = st.session_state["pagina"]

if pagina == "comparar":
    st.subheader("Escolha quem é melhor entre os três:")
    recent_players = get_recent_players(progress["history"])
    trio = get_next_trio_heuristic(all_players, progress["preferences"], progress["history"], k=3, exclude=recent_players)

    votos = {}
    cols = st.columns(3)
    for i, jogador in enumerate(trio):
        nome = jogador["PLAYER NAME"]
        with cols[i]:
            st.markdown(f"### {nome}")
            st.markdown(f"**Tier**: {jogador.get('TIERS', '?')}")
            votos[nome] = st.radio("Escolha:", ["", "Start", "Bench", "Drop"], key=f"voto_{i}")

    if st.button("✅ Confirmar escolha"):
        if sorted(votos.values()) != ["Bench", "Drop", "Start"]:
            st.warning("Você deve selecionar exatamente um Start, um Bench e um Drop.")
        else:
            ordem = {"Start": 2, "Bench": 1, "Drop": 0}
            trio_ordenado = sorted(votos.items(), key=lambda x: ordem[x[1]], reverse=True)
            for i in range(3):
                for j in range(i+1, 3):
                    melhor, pior = trio_ordenado[i][0], trio_ordenado[j][0]
                    progress["preferences"].append((melhor, pior))
                    progress["history"].append(tuple(sorted((melhor, pior))))
            save_user_progress(user, position, progress)
            st.rerun()

    st.markdown("---")
    total_jogadores = len(players_df)
    comparados = len(set(p for pair in progress["preferences"] for p in pair))
    total_pares = len(progress["history"])
    minimo_sugerido = int(total_jogadores * math.log2(total_jogadores))
    maximo_teorico = total_jogadores * (total_jogadores - 1) // 2

    st.markdown(f"✅ Jogadores já comparados: **{comparados}/{total_jogadores}**")
    st.markdown(f"🔁 Comparações feitas: **{total_pares}**")
    st.markdown(f"📊 Mínimo sugerido para bom ranking: **{minimo_sugerido}**")
    st.markdown(f"🧪 Máximo teórico: **{maximo_teorico}**")

    if st.button("📋 Ver ranking parcial"):
        st.session_state["pagina"] = "ranking"
        st.rerun()

elif pagina == "ranking":
    st.subheader(f"📋 Ranking de {position}")
    graph = build_graph(progress["preferences"])
    try:
        ordenado = topological_rank(graph)
        score = {nome: i for i, nome in enumerate(ordenado)}
        df = players_df.set_index("PLAYER NAME").loc[ordenado].copy()
        df["Ranking"] = df.index.map(score)
        df["Ranking"] = df["Ranking"] + 1
        df = df.reset_index()
        df = df.sort_values("Ranking")
        cols_para_exibir = ["Ranking", "PLAYER NAME", "TIERS", "RK", "AVG.", "ECR VS ADP"]
        st.dataframe(df[cols_para_exibir])

        csv = df[cols_para_exibir].to_csv(index=False)
        st.download_button("⬇️ Baixar ranking em CSV", data=csv, file_name=f"{user}_{position}_ranking.csv", mime="text/csv")
    except nx.NetworkXUnfeasible:
        st.error("⚠️ Detetado conflito nas comparações. Gerando sugestões para resolver...")
        sugestoes = suggest_repair_comparisons(graph, progress["preferences"])
        if sugestoes:
            st.markdown("🔄 Compare os seguintes jogadores para melhorar o ranking:")
            for a, b in sugestoes[:3]:
                st.markdown(f"- {a} vs {b}")
        else:
            st.warning("Não foi possível sugerir pares. Tente comparar mais jogadores.")

    if st.button("🔙 Voltar para comparar"):
        st.session_state["pagina"] = "comparar"
        st.rerun()
