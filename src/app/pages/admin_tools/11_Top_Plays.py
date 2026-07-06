from __future__ import annotations

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, football_card, compact_football_table
from src.app.utils.sqlite_runtime import cached_table, filter_by_column_value, sort_by_confidence, unique_options, show_database_download

configure_page("Top Plays", "🔥")
refresh_chip()

football_df = sort_by_confidence(cached_table("football_ensemble_predictions"))

compact_header(
    "TOP PLAYS",
    "Highest-ranked football signals.",
    "Top plays are selected directly from SQLite football ensemble predictions.",
    tags=["Football", "Top signals", "SQLite"],
    metrics=[
        {"label": "Signals", "value": len(football_df), "note": "rows"},
        {"label": "Leagues", "value": football_df["League"].nunique() if "League" in football_df.columns else 0, "note": "covered"},
    ],
)

league_options = unique_options(football_df, "League")
selected_league = st.selectbox("League", league_options)
view_df = filter_by_column_value(football_df, "League", selected_league)

kpi_grid([
    {"icon": "🔥", "title": "Top plays", "value": min(len(view_df), 20), "sub": "shown"},
    {"icon": "⚽", "title": "Filtered signals", "value": len(view_df), "sub": "rows"},
    {"icon": "🌍", "title": "Selected league", "value": selected_league, "sub": "filter"},
])

section_title("Top signal cards", "🔥")
for rank, (_, row) in enumerate(view_df.head(20).iterrows(), start=1):
    football_card(row, rank=rank)

section_title("Top plays table", "▣")
compact_football_table(view_df, limit=150)
show_database_download(view_df, "top_football_plays.csv")
