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

def get_next_trio(remaining, history, all_players):
    attempts = 0
    while attempts < 1000:
        trio = tuple(sorted(random.sample(remaining, 3)))
        if trio not in history:
            return trio
        attempts += 1

    # Fallback: sorteia de todos se não achar inédito
    while True:
        trio = tuple(sorted(random.sample(all_players, 3)))
        if trio not in history:
            return trio
