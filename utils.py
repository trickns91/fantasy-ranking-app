import pandas as pd
import random
import os
import json

DATA_DIR = "data"
PROGRESS_DIR = "progress"
os.makedirs(PROGRESS_DIR, exist_ok=True)

def load_players(position):
    path = f"{DATA_DIR}/{position}.csv"
    df = pd.read_csv(path)
    return df.head(32 if position in ["QB", "TE"] else 100)

def load_user_progress(user, position):
    path = f"{PROGRESS_DIR}/{user}_{position}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def save_user_progress(user, position, data):
    path = f"{PROGRESS_DIR}/{user}_{position}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def get_next_trio_heuristic(remaining, preferences, history, k=4):
    from collections import Counter

    # Contar quantas vezes cada jogador já apareceu como preferido
    count = Counter()
    for a, b in preferences:
        count[a] += 1
        count[b] += 0  # garante presença

    # Jogadores com menos comparações recebem prioridade
    sorted_players = sorted(remaining, key=lambda x: count[x])

    # Evitar trios repetidos do histórico
    attempts = 0
    while attempts < 2000:
        candidates = sorted_players[:max(k * 3, k + 3)]  # grupo mais amplo
        sample = tuple(sorted(random.sample(candidates, k)))
        if sample not in history:
            return sample
        attempts += 1

    # Fallback: sorteia de todos se não achar inédito
    while True:
        trio = tuple(sorted(random.sample(remaining, k)))
        if trio not in history:
            return trio
