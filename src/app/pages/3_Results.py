from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.utils.sqlite_runtime import cached_table, sort_by_date, count_rows, latest_label
from src.app.components.website import (
    hero, mini_cards, section_label, result_row, empty_message,
    friendly_table, page_footer,
)

configure_page("Results", "📋")
refresh_chip()

@st.cache_data(ttl=300, show_spinner=False)
def load_results():
    lottery = sort_by_date(cached_table("lottery_history", limit=500))
    football = sort_by_date(cached_table("football_history", limit=500))
    scored = sort_by_date(cached_table("football_backtest_history", limit=5000))
    return lottery, football, scored

lottery, football, scored = load_results()

hero(
    "Recent results.",
    "A clean place to review recent lottery draws and football outcomes without opening spreadsheets.",
    eyebrow="Results",
    chips=["Recent draws", "Past matches", "Simple view"],
    metrics=[
        {"value": f"{len(lottery):,}", "label": "Lottery rows shown"},
        {"value": f"{len(football):,}", "label": "Football rows shown"},
        {"value": f"{len(scored):,}", "label": "Scored picks"},
        {"value": latest_label(lottery, "DrawDate", "GameName"), "label": "Latest draw"},
    ],
)

mini_cards([
    {"icon": "🎲", "label": "Lottery results", "value": f"{count_rows('lottery_history'):,}", "note": "total stored"},
    {"icon": "⚽", "label": "Football results", "value": f"{count_rows('football_history'):,}", "note": "total stored"},
    {"icon": "📌", "label": "Latest draw", "value": latest_label(lottery, "DrawDate", "GameName"), "note": "newest result"},
    {"icon": "🧾", "label": "Scored picks", "value": f"{count_rows('football_backtest_history'):,}", "note": "runtime sample"},
])

left, right = st.columns([1.05, .95], gap="large")

with left:
    section_label("Lottery results", "Recent draw cards.")
    if lottery.empty:
        empty_message("No lottery results", "Lottery results are not available yet.")
    else:
        for _, row in lottery.head(10).iterrows():
            result_row(row)

with right:
    section_label("Football results", "Recent football rows in a simple table.")
    friendly_table(
        football,
        ["MatchDate", "Season", "League", "HomeTeam", "AwayTeam", "HomeGoals", "AwayGoals", "Result"],
        height=560,
        limit=80,
    )

page_footer()
