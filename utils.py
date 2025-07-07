import pandas as pd
import os
import json
import random
import itertools

DATA_DIR = "data"
PROGRESS_DIR = "progress"

def load_players(position):
    path = os.path.join(DATA_DIR, f"{position.upper()}.csv")
    df = pd.read_csv(path)
    df = df.head(24) if position.upper() in ["QB", "TE"] else df.head(48)
    return df

def load_user_progress(user, position):
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    path = os.path.join(PROGRESS_DIR, f"{user}_{position.upper()}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"preferences": [], "history": [], "ranked": []}

def save_user_progress(user, position, progress):
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    path = os.path.join(PROGRESS_DIR, f"{user}_{position.upper()}.json")
    with open(path, "w") as f:
        json.dump(progress, f)

def get_recent_players(history, max_recent=6):
    recent = []
    for pair in reversed(history):
        recent.extend(pair)
        if len(recent) >= max_recent:
            break
    return list(set(recent[-max_recent:]))

def get_next_trio_heuristic(players, preferences, history, k=3, tiers=None, exclude=[]):
    history_set = set(tuple(sorted(p)) for p in history)
    all_pairs = set(tuple(sorted(pair)) for pair in itertools.combinations(players, 2))
    remaining_pairs
