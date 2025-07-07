import pandas as pd
import os
import json
import random
import itertools

DATA_DIR = "data"
USER_DIR = "user_data"

def load_players(position):
    filepath = os.path.join(DATA_DIR, f"{position}.csv")
    df = pd.read_csv(filepath)
    df = df.dropna(subset=["PLAYER NAME"])
    if position in ["QB", "TE"]:
        df = df.head(24)
    else:  # RB, WR
        df = df.head(48)
    return df

def load_user_progress(user, position):
    os.makedirs(USER_DIR, exist_ok=True)
    filepath = os.path.join(USER_DIR, f"{user}_{position}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
            # Garantir que history é sempre tuple ordenado
            data["history"] = [tuple(sorted(p)) for p in data.get("history", [])]
            return data
    return {"preferences": [], "history": [], "ranked": []}

def save_user_progress(user, position, progress):
    filepath = os.path.join(USER_DIR, f"{user}_{position}.json")
    data = {
        "preferences": progress["preferences"],
        "history": [list(p) for p in progress["history"]],
        "ranked": progress.get("ranked", [])
    }
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def get_recent_players(history, max_recent=6):
    flat = [p for pair in reversed(history[-max_recent:]) for p in pair]
    return list(set(flat[-max_recent:]))

def get_next_trio_heuristic(players, preferences, history, k=3, tiers=None, exclude=[]):
    history_set = set(tuple(sorted(p)) for p in history)
    available = [p for p in players if p not in exclude]
    
    if len(available) < k:
        available = players

    if tiers:
        tier_dict = {p: int(t) if str(t).isdigit() else 99 for p, t in zip(players, tiers)}
        available.sort(key=lambda x: tier_dict.get(x, 99))

    random.shuffle(available)
    return get_trio_from_pool(available, history_set, k)

def get_trio_from_pool(pool, history_set, k=3):
    for trio in itertools.combinations(pool, k):
        pairings = set(tuple(sorted([trio[i], trio[j]])) for i in range(k) for j in range(i + 1, k))
        if not pairings.issubset(history_set):
            return list(trio)
    return random.sample(pool, k)
