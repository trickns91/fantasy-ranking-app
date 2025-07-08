
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
    else:
        df = df.head(48)
    return df

def load_user_progress(user, position):
    os.makedirs(USER_DIR, exist_ok=True)
    filepath = os.path.join(USER_DIR, f"{user}_{position}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    else:
        return {"preferences": [], "history": [], "ranked": []}

def save_user_progress(user, position, progress):
    os.makedirs(USER_DIR, exist_ok=True)
    filepath = os.path.join(USER_DIR, f"{user}_{position}.json")
    with open(filepath, "w") as f:
        json.dump(progress, f)

def get_recent_players(history, max_recent=6):
    flat = [p for pair in history[-max_recent:] for p in pair]
    return list(set(flat))

def get_next_trio_heuristic(players, preferences, history, k=3, tiers=None, exclude=[]):
    history_set = set(tuple(sorted(p)) for p in history)
    available = [p for p in players if p not in exclude]
    if len(available) < k:
        available = players
    if tiers:
        tier_dict = {p: int(t) if str(t).isdigit() else 99 for p, t in zip(players, tiers)}
        available.sort(key=lambda x: tier_dict.get(x, 99))
    pool = [p for p in available if p not in exclude]
    random.shuffle(pool)
    for trio in itertools.combinations(pool, k):
        pairings = set(tuple(sorted([trio[i], trio[j]])) for i in range(k) for j in range(i+1, k))
        if not pairings.issubset(history_set):
            return list(trio)
    return random.sample(pool, k)
