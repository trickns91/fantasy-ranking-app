
import pandas as pd
import os
import json
import random
import itertools
import networkx as nx
from collections import defaultdict

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
    flat = [p for pair in history for p in pair]
    return list(dict.fromkeys(flat[::-1]))[:max_recent]

def get_trio_from_pool(candidates, preferences, history, k=3):
    def num_comparisons(p):
        return sum([p in pair for pair in history])

    candidates = sorted(candidates, key=lambda x: (x["TIERS"], num_comparisons(x["PLAYER NAME"])))
    seen = set(tuple(sorted(pair)) for pair in history)

    for trio in itertools.combinations(candidates, 3):
        pairings = set(itertools.combinations([p["PLAYER NAME"] for p in trio], 2))
        if not pairings.issubset(seen):
            return list(trio)

    return random.sample(candidates, k) if len(candidates) >= k else candidates

def get_next_trio_heuristic(all_players, preferences, history, k=3, tiers=None, exclude=None):
    exclude = exclude or []
    ranked_names = set(p for pair in preferences for p in pair)
    candidates = [p for p in all_players if p["PLAYER NAME"] not in exclude and p["PLAYER NAME"] not in ranked_names]
    if not candidates:
        candidates = all_players
    return get_trio_from_pool(candidates, preferences, history, k)

def build_graph(preferences):
    G = nx.DiGraph()
    for winner, loser in preferences:
        G.add_edge(winner, loser)
    return G

def topological_rank(graph):
    return list(nx.topological_sort(graph))

def suggest_repair_comparisons(graph, preferences):
    try:
        nx.find_cycle(graph, orientation="original")
    except nx.exception.NetworkXNoCycle:
        return []

    components = list(nx.strongly_connected_components(graph))
    suggestions = []
    for comp in components:
        if len(comp) > 1:
            pairs = list(itertools.combinations(comp, 2))
            already_compared = set(tuple(sorted(p)) for p in preferences)
            new_pairs = [p for p in pairs if tuple(sorted(p)) not in already_compared]
            suggestions.extend(new_pairs)
    return suggestions
