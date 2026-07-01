import pandas as pd
import os

def load_forward_data(filepath="skaters.csv", min_games=30):
    df = pd.read_csv(filepath)
    forwards = df[
        (df["position"].isin(["C", "L", "R"])) &
        (df["situation"] == "all") &
        (df["games_played"] >= min_games)
    ].copy()
    return forwards

def calculate_goals_above_expected(forwards):
    """Add a column showing actual goals minus expected goals."""
    forwards["goals_above_expected"] = forwards["I_F_goals"] - forwards["I_F_xGoals"]
    return forwards

def get_top_overperformers(forwards, n=10):
    return forwards.sort_values("goals_above_expected", ascending=False)[
        ["name", "team", "I_F_goals", "I_F_xGoals", "goals_above_expected"]
    ].head(n)

def get_top_underperformers(forwards, n=10):
    return forwards.sort_values("goals_above_expected", ascending=True)[
        ["name", "team", "games_played", "I_F_goals", "I_F_xGoals", "goals_above_expected"]
    ].head(n)

def download_season(season, folder="data"):
    """Download a season's skater CSV from MoneyPuck if not already present."""
    os.makedirs(folder, exist_ok=True)
    filepath = f"{folder}/skaters_{season}.csv"
    if not os.path.exists(filepath):
        url = f"https://moneypuck.com/moneypuck/playerData/seasonSummary/{season}/regular/skaters.csv"
        import requests
        r = requests.get(url)
        with open(filepath, "wb") as f:
            f.write(r.content)
        print(f"Downloaded {season}")
    else:
        print(f"Already have {season}")
    return filepath

def load_multiple_seasons(seasons, min_games=30):
    dfs = []
    for season in seasons:
        filepath = download_season(season)
        df = pd.read_csv(filepath)
        df["season"] = season
        forwards = df[
            (df["position"].isin(["C", "L", "R"])) &
            (df["situation"] == "all") &
            (df["games_played"] >= min_games)
        ].copy()
        dfs.append(forwards)
    return pd.concat(dfs, ignore_index=True)

def get_consistent_performers(forwards, min_seasons=3):
    """Find players who consistently over or underperform their xG across multiple seasons."""
    grouped = forwards.groupby("name").agg(
        seasons=("season", "count"),
        total_goals=("I_F_goals", "sum"),
        total_xGoals=("I_F_xGoals", "sum"),
        avg_gax=("goals_above_expected", "mean"),
        total_gax=("goals_above_expected", "sum"),
        teams=("team", lambda x: ", ".join(x.unique()))
    ).reset_index()

    # Filter to players with enough seasons
    grouped = grouped[grouped["seasons"] >= min_seasons]
    return grouped

def load_salary_data(filepath="data/contracts_2024.csv"):
    salary = pd.read_csv(filepath)
    salary = salary[salary["Pos.grouped"] == "F"].copy()
    salary["cap_hit"] = (
        salary["AAV"]
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )
    salary = salary[["Player.ascii", "cap_hit"]].rename(columns={"Player.ascii": "name"})
    
    # Deduplicate — keep highest cap hit per player (most recent/relevant contract)
    salary = salary.sort_values("cap_hit", ascending=False).drop_duplicates(subset="name")
    return salary

def merge_salary(consistent, salary):
    """Join salary onto consistent performers dataframe."""
    merged = consistent.merge(salary, on="name", how="left")
    
    # Calculate dollars per xGoal (efficiency metric)
    merged["cap_per_xGoal"] = merged["cap_hit"] / merged["total_xGoals"]
    
    # Calculate value score: GAX relative to cap hit (higher = better value)
    merged["value_score"] = merged["total_gax"] / (merged["cap_hit"] / 1_000_000)
    
    return merged

if __name__ == "__main__":
    seasons = [2021, 2022, 2023, 2024, 2025]
    forwards = load_multiple_seasons(seasons)
    forwards = calculate_goals_above_expected(forwards)
    consistent = get_consistent_performers(forwards, min_seasons=3)
    
    salary = load_salary_data()
    merged = merge_salary(consistent, salary)

# Filter out ELC players (cap hit under $1M) for cleaner analysis
    non_elc = merged[merged["cap_hit"] >= 1_000_000].dropna(subset=["cap_hit"])

    print("=== Best Value Forwards (non-ELC) ===")
    print(non_elc.sort_values("value_score", ascending=False)[
        ["name", "seasons", "cap_hit", "total_gax", "value_score"]
    ].head(10).to_string())

    print("\n=== Worst Value Forwards ===")
    print(non_elc.sort_values("value_score", ascending=True)[
        ["name", "seasons", "cap_hit", "total_gax", "value_score"]
    ].head(10).to_string())