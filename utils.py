import pandas as pd
import os
import json
import random

DATA_PATH = "data"
USER_DATA_PATH = "user_data"

def load_players(position):
    return pd.read_csv(f"{DATA_PATH}/{position}.csv")

def load_user_progress(user, position):
    filepath = f"{USER_DATA_PATH}/{user}_{position}.json"
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return None

def save_user_progress(user, position, data):
    os.makedirs(USER_DATA_PATH, exist_ok=True)
    filepath = f"{USER_DATA_PATH}/{user}_{position}.json"
    with open(filepath, "w") as f:
        json.dump(data, f)

def get_next_trio(available, history, scores):
    """
    Retorna um trio de jogadores baseado em:
    - Jogadores ainda não ranqueados
    - Evita combinações já apresentadas
    - Prioriza jogadores com pontuação parecida ou sem pontuação
    """
    # Priorizar jogadores com pontuação indefinida
    unknowns = [p for p in available if p not in scores]
    if len(unknowns) >= 3:
        random.shuffle(unknowns)
        trio = unknowns[:3]
        if tuple(sorted(trio)) not in history:
            return trio

    # Se não há desconhecidos, pegar os com pontuação mais próxima
    scored = [(p, scores.get(p, 0)) for p in available]
    scored.sort(key=lambda x: x[1])
    for i in range(len(scored) - 2):
        trio = [scored[i][0], scored[i+1][0], scored[i+2][0]]
        if tuple(sorted(trio)) not in history:
            return trio

    # Se tudo falhar, pegar trio aleatório nunca usado
    attempts = 0
    while attempts < 20:
        trio = random.sample(available, 3)
        if tuple(sorted(trio)) not in history:
            return trio
        attempts += 1

    # Último recurso
    return random.sample(available, 3)
