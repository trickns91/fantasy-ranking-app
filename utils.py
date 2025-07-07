import pandas as pd
import os
import random
import json

DATA_FOLDER = "data"
SAVE_FOLDER = "progress"

def load_players(position):
    filepath = os.path.join(DATA_FOLDER, f"{position}.csv")
    df = pd.read_csv(filepath)
    df = df.dropna(subset=["PLAYER NAME"])
    df = df.head({
        "QB": 24,
        "RB": 100,
        "WR": 100,
        "TE": 24
    }[position])
    return df

def save_user_progress(user, position, progress):
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    filepath = os.path.join(SAVE_FOLDER, f"{user}_{position}.json")
    with open(filepath, "w") as f:
        json.dump(progress, f)

def load_user_progress(user, position):
    filepath = os.path.join(SAVE_FOLDER, f"{user}_{position}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    else:
        return {"preferences": [], "history": [], "ranked": []}

def get_recent_players(history, max_recent=6):
    flat = [p for pair in history[-max_recent:] for p in pair]
    return list(set(flat))

def get_next_trio_heuristic(players, preferences, history, k=3, tiers=None, exclude=None):
    if not exclude:
        exclude = []

    all_pairs = {(a, b) for a in players for b in players if a != b}
    done_pairs = set(tuple(sorted(pair)) for pair in history)
    remaining_pairs = list(all_pairs - done_pairs)

    score = {p: 0 for p in players}
    for a, b in preferences:
        score[a] += 1

    # Mapear jogadores por tier
    if tiers:
        tier_map = {}
        for i, p in enumerate(players):
            try:
                tier_map.setdefault(int(tiers[i]), []).append(p)
            except:
                continue
        sorted_tiers = sorted(tier_map.keys())
        for tier in sorted_tiers:
            candidates = tier_map[tier]
            trio = get_trio_from_pool(candidates, preferences, history, exclude, k)
            if trio:
                return trio

    # Fallback total
    return get_trio_from_pool(players, preferences, history, exclude, k)

def get_trio_from_pool(pool, preferences, history, exclude, k):
    attempts = 100
    tried = set()
    for _ in range(attempts):
        trio = tuple(sorted(random.sample(pool, k)))
        if any(p in exclude for p in trio):
            continue
        pairings = set(tuple(sorted((a, b))) for i, a in enumerate(trio) for b in trio[i+1:])
        if not pairings.issubset(set(history)):
            if trio not in tried:
                return list(trio)
        tried.add(trio)
    return None
