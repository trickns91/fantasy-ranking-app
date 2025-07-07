import pandas as pd
import os

def load_players(position):
    df = pd.read_csv(f"data/{position}.csv")
    return df

def save_user_ranking(user_name, position, df):
    path = f"user_rankings/{user_name}_{position}.csv"
    os.makedirs("user_rankings", exist_ok=True)
    df.to_csv(path, index=False)

def compare_with_fantasypros(position, user_df):
    original_df = pd.read_csv(f"data/{position}.csv")
    original_df["FANTASYPROS_RANK"] = range(1, len(original_df) + 1)

    merged = user_df.merge(original_df[["PLAYER NAME", "FANTASYPROS_RANK"]], on="PLAYER NAME", how="left")
    merged["DIFFERENCE"] = merged["FANTASYPROS_RANK"] - merged["RANK"]
    return merged
