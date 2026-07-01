import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from analyze_skaters import (
    load_multiple_seasons,
    calculate_goals_above_expected,
    get_consistent_performers,
    load_salary_data,
    merge_salary
)

st.set_page_config(page_title="NHL Forward Valuation", layout="wide")
st.title("NHL Forward Valuation Dashboard")
st.markdown("Identifying undervalued forwards using Goals Above Expected (GAX)")

@st.cache_data
def load_data():
    seasons = [2021, 2022, 2023, 2024, 2025]
    forwards = load_multiple_seasons(seasons)
    forwards = calculate_goals_above_expected(forwards)
    return forwards

@st.cache_data
def load_salary():
    return load_salary_data()

forwards = load_data()
salary = load_salary()

# Sidebar filters
st.sidebar.header("Filters")
min_seasons = st.sidebar.slider("Minimum seasons", 1, 5, 3)
min_cap = st.sidebar.slider("Minimum cap hit ($M)", 0, 10, 1)

consistent = get_consistent_performers(forwards, min_seasons=min_seasons)
merged = merge_salary(consistent, salary)
non_elc = merged[merged["cap_hit"] >= min_cap * 1_000_000].dropna(subset=["cap_hit"])

# Tabs
tab1, tab2, tab3 = st.tabs(["GAX Rankings", "Salary Value", "Player Lookup"])

with tab1:
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

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Best Value Forwards")
        st.dataframe(
            non_elc.sort_values("value_score", ascending=False)[
                ["name", "seasons", "cap_hit", "total_gax", "value_score"]
            ].head(15).reset_index(drop=True),
            use_container_width=True
        )
    with col2:
        st.subheader("Worst Value Forwards")
        st.dataframe(
            non_elc.sort_values("value_score", ascending=True)[
                ["name", "seasons", "cap_hit", "total_gax", "value_score"]
            ].head(15).reset_index(drop=True),
            use_container_width=True
        )
    st.subheader("Cap Hit vs Goals Above Expected")

    fig2, ax2 = plt.subplots(figsize=(12, 7))

    # Plot all players as dots
    ax2.scatter(
        non_elc["cap_hit"] / 1_000_000,
        non_elc["total_gax"],
        alpha=0.6,
        color="#4a90d9",
        s=60
    )

    # Add a horizontal line at y=0
    ax2.axhline(y=0, color="white", linewidth=0.8, linestyle="--", alpha=0.5)

    # Label notable outliers (top 5 and bottom 5 value scores)
    top5 = non_elc.nlargest(5, "value_score")
    bot5 = non_elc.nsmallest(5, "value_score")
    labels = pd.concat([top5, bot5])

    for _, row in labels.iterrows():
        ax2.annotate(
            row["name"],
            (row["cap_hit"] / 1_000_000, row["total_gax"]),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=7,
            color="white"
        )

    ax2.set_xlabel("Cap Hit ($M)", color="white")
    ax2.set_ylabel("Total Goals Above Expected (5 seasons)", color="white")
    ax2.set_title("Forward Value: Cap Hit vs GAX", color="white")
    ax2.tick_params(colors="white")
    ax2.set_facecolor("#0e1117")
    fig2.patch.set_facecolor("#0e1117")

    st.pyplot(fig2)

with tab3:
    st.subheader("Player Lookup")
    player_names = sorted(forwards["name"].unique())
    selected_player = st.selectbox("Search for a player", player_names)

    player_data = forwards[forwards["name"] == selected_player][
        ["season", "team", "games_played", "I_F_goals", "I_F_xGoals", "goals_above_expected"]
    ].sort_values("season")

    st.dataframe(player_data.reset_index(drop=True), use_container_width=True)

    if len(player_data) > 1:
        fig, ax = plt.subplots(figsize=(8, 4))
        colors = ["#e63946" if g < 0 else "#2a9d8f" for g in player_data["goals_above_expected"]]
        ax.bar(player_data["season"], player_data["goals_above_expected"], color=colors)
        ax.axhline(y=0, color="white", linewidth=0.8, linestyle="--", alpha=0.5)
        ax.set_title(f"{selected_player} — Goals Above Expected by Season", color="white")
        ax.set_xlabel("Season", color="white")
        ax.set_ylabel("Goals Above Expected", color="white")
        ax.tick_params(colors="white")
        ax.set_xticks(player_data["season"].values)
        ax.set_xticklabels([str(s) for s in player_data["season"].values])
        ax.set_facecolor("#0e1117")
        fig.patch.set_facecolor("#0e1117")
        st.pyplot(fig)
    else:
        st.info("Need at least 2 seasons of data to show trend chart.")