from __future__ import annotations

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, football_card, compact_football_table, dataframe_card
from src.app.utils.sqlite_runtime import (
    cached_table,
    filter_by_column_value,
    sort_by_best_date,
    sort_by_confidence,
    unique_options,
)

configure_page("Football Home", "⚽")
refresh_chip()

history_df = sort_by_best_date(cached_table("football_history"))
ensemble_df = sort_by_confidence(cached_table("football_ensemble_predictions"))
fixtures_df = sort_by_best_date(cached_table("football_fixtures"), ascending=True)

compact_header(
    "FOOTBALL INTELLIGENCE",
    "Football warehouse view.",
    "Historical results, ensemble signals and fixture status from SQLite.",
    tags=["Football", "SQLite", "Model signals"],
    metrics=[
        {"label": "History", "value": f"{len(history_df):,}", "note": "matches"},
        {"label": "Signals", "value": f"{len(ensemble_df):,}", "note": "predictions"},
        {"label": "Fixtures", "value": f"{len(fixtures_df):,}", "note": "upcoming"},
        {"label": "Leagues", "value": ensemble_df["League"].nunique() if "League" in ensemble_df.columns else 0, "note": "tracked"},
    ],
)

league_options = unique_options(ensemble_df, "League")
selected_league = st.selectbox("League", league_options)
view_df = filter_by_column_value(ensemble_df, "League", selected_league)

kpi_grid([
    {"icon": "⚽", "title": "Selected", "value": selected_league, "sub": "league"},
    {"icon": "🔥", "title": "Top signals", "value": len(view_df), "sub": "filtered"},
    {"icon": "📚", "title": "History", "value": f"{len(history_df):,}", "sub": "result rows"},
    {"icon": "📅", "title": "Fixtures", "value": f"{len(fixtures_df):,}", "sub": "fixture rows"},
])

left, right = st.columns([1.05, 0.95], gap="large")
with left:
    section_title("Top football signals", "🔥")
    for rank, (_, row) in enumerate(view_df.head(8).iterrows(), start=1):
        football_card(row, rank=rank)

with right:
    section_title("Upcoming fixtures", "📅")
    dataframe_card(fixtures_df, height=300, limit=40, empty_title="No fixtures")

    section_title("Recent football results", "▣")
    dataframe_card(history_df, height=300, limit=40, empty_title="No football history")

section_title("Football signal table", "▣")
compact_football_table(view_df, limit=120)
