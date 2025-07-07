import os
import pandas as pd
import json
from collections import Counter, defaultdict
import random

DATA_PATH = "data"
USER_DATA_PATH = "user_data"

def load_players(position):
    df = pd.read_csv(f"{DATA_PATH}/{position}.csv")
    df["TIERS"] = pd.to_numeric(df["TIERS"], errors="coerce").fillna(99).astype(int)
    return df

def load_user_progress(user, position):
    os.makedirs(USER_DATA_PATH, exist_ok=True)
    path = f"{USER_DATA_PATH}/{user}_{position}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    else:
        return {"preferences": [], "history": []}

def save_user_progress(user, position, progress):
    os.makedirs(USER_DATA_PATH, exist_ok=True)
    path = f"{USER_DATA_PATH}/{user}_{position}.json"
    with open(path, "w") as f:
        json.dump(progress, f)

def get_next_trio_heuristic(players, preferences, history, k=3, tiers=None):
    if not tiers:
        tiers = {p: 1 for p in players}  # fallback: tudo tier 1

    # Contar comparações por jogador
    counts = Counter()
    for a, b in preferences:
        counts[a] += 1
        counts[b] += 1

    # Organizar jogadores por tier
    tier_groups = defaultdict(list)
    for p in players:
        tier = tiers.get(p, 99)
        tier_groups[tier].append(p)

    # Ordenar tiers do melhor (1) ao pior
    for tier in sorted(tier_groups):
        grupo_tier = tier_groups[tier]
        grupo_restante = [p for p in grupo_tier if tuple(sorted((p,))) not in history]

        if len(grupo_restante) >= k:
            candidatos = sorted(grupo_restante, key=lambda x: counts[x])[:12]
            random.shuffle(candidatos)
            return candidatos[:k]

    # Se todos os tiers já foram trabalhados, sortear entre tiers
    candidatos = sorted(players, key=lambda x: counts[x])[:20]
    random.shuffle(candidatos)
    tentativa = tuple(sorted(candidatos[:k]))
    if tentativa not in history:
        return list(tentativa)

    # fallback final
    for _ in range(100):
        tentativa = tuple(sorted(random.sample(players, k)))
        if tentativa not in history:
            return list(tentativa)

    return []  # nada novo encontrado
