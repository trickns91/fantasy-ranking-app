import os
import pandas as pd
import json
import random

DATA_DIR = "data"
USER_DATA_DIR = "user_data"

def load_players(position):
    file_path = os.path.join(DATA_DIR, f"{position}.csv")
    df = pd.read_csv(file_path)
    if position in ["RB", "WR"]:
        return df.head(100)
    elif position in ["QB", "TE"]:
        return df.head(24)
    else:
        return df

def load_user_progress(user, position):
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    file_path = os.path.join(USER_DATA_DIR, f"{user}_{position}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {"preferences": [], "history": [], "ranked": []}

def save_user_progress(user, position, data):
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    file_path = os.path.join(USER_DATA_DIR, f"{user}_{position}.json")
    with open(file_path, "w") as f:
        json.dump(data, f)

def get_recent_players(history, max_recent=6):
    recent_flat = [p for pair in history[-max_recent:] for p in pair]
    return list(set(recent_flat))

def get_next_trio_heuristic(players, preferences, history, k=3, tiers=None, exclude=None):
    if exclude is None:
        exclude = []

    history_pairs = set(tuple(sorted(pair)) for pair in history)
    all_pairs = set(tuple(sorted([a, b])) for i, a in enumerate(players) for b in players[i + 1:] if a != b)
    remaining_pairs = all_pairs - history_pairs

    unused = [p for p in players if any(p in pair for pair in remaining_pairs)]
    candidates = [p for p in unused if p not in exclude]

    if len(candidates) < k:
        candidates = [p for p in players if p not in exclude]

    if len(candidates) < k:
        return None

    return random.sample(candidates, k)
