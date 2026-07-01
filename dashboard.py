import streamlit as st
import pandas as pd
from analyze_skaters import load_multiple_seasons, calculate_goals_above_expected, get_consistent_performers

st.set_page_config(page_title="NHL Forward Valuation", layout="wide")

st.title("NHL Forward Valuation Dashboard")
st.markdown("Identifying undervalued forwards using Goals Above Expected (GAX)")

# Load data
@st.cache_data
def load_data():
    seasons = [2021, 2022, 2023, 2024, 2025]
    forwards = load_multiple_seasons(seasons)
    forwards = calculate_goals_above_expected(forwards)
    return forwards

forwards = load_data()
consistent = get_consistent_performers(forwards, min_seasons=3)

# Sidebar filters
st.sidebar.header("Filters")
min_seasons = st.sidebar.slider("Minimum seasons", 1, 5, 3)
consistent = get_consistent_performers(forwards, min_seasons=min_seasons)

# Two columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("Consistently Overperforming")
    st.dataframe(
        consistent.sort_values("total_gax", ascending=False)[
            ["name", "seasons", "teams", "total_goals", "total_xGoals", "total_gax", "avg_gax"]
        ].head(15).reset_index(drop=True),
        use_container_width=True
    )

with col2:
    st.subheader("Consistently Underperforming (Moneyball Targets)")
    st.dataframe(
        consistent.sort_values("total_gax", ascending=True)[
            ["name", "seasons", "teams", "total_goals", "total_xGoals", "total_gax", "avg_gax"]
        ].head(15).reset_index(drop=True),
        use_container_width=True
    )

# Player lookup
st.subheader("Player Lookup")
player_names = sorted(forwards["name"].unique())
selected_player = st.selectbox("Search for a player", player_names)

player_data = forwards[forwards["name"] == selected_player][
    ["season", "team", "games_played", "I_F_goals", "I_F_xGoals", "goals_above_expected"]
].sort_values("season")

st.dataframe(player_data.reset_index(drop=True), use_container_width=True)

import matplotlib.pyplot as plt

if len(player_data) > 1:
    fig, ax = plt.subplots(figsize=(8, 4))
    
    colors = ["#e63946" if g < 0 else "#2a9d8f" for g in player_data["goals_above_expected"]]
    bars = ax.bar(player_data["season"], player_data["goals_above_expected"], color=colors)
    
    ax.axhline(y=0, color="white", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_title(f"{selected_player} — Goals Above Expected by Season", color="white")
    ax.set_xlabel("Season", color="white")
    ax.set_ylabel("Goals Above Expected", color="white")
    ax.set_xticks(player_data["season"].values)
    ax.set_xticklabels([str(s) for s in player_data["season"].values])
    ax.tick_params(colors="white")
    ax.set_facecolor("#0e1117")
    fig.patch.set_facecolor("#0e1117")
    
    st.pyplot(fig)
else:
    st.info("Need at least 2 seasons of data to show trend chart.")