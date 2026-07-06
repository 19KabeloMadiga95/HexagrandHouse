from __future__ import annotations

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, dataframe_card, compact_football_table
from src.app.utils.sqlite_runtime import cached_table, filter_by_column_value, sort_by_confidence, unique_options

configure_page("League Analytics", "🌍")
refresh_chip()

history_df = cached_table("football_history")
ensemble_df = sort_by_confidence(cached_table("football_ensemble_predictions"))

if not ensemble_df.empty and "League" in ensemble_df.columns:
    league_summary = (
        ensemble_df.groupby("League", dropna=False)
        .size()
        .reset_index(name="PredictionCount")
        .sort_values("PredictionCount", ascending=False)
    )
else:
    league_summary = pd.DataFrame(columns=["League", "PredictionCount"])

if not history_df.empty and "League" in history_df.columns:
    history_summary = (
        history_df.groupby("League", dropna=False)
        .size()
        .reset_index(name="ResultCount")
        .sort_values("ResultCount", ascending=False)
    )
else:
    history_summary = pd.DataFrame(columns=["League", "ResultCount"])

compact_header(
    "LEAGUE ANALYTICS",
    "Coverage and signal density.",
    "League-level summaries calculated directly from SQLite tables.",
    tags=["League coverage", "SQLite", "Football"],
    metrics=[
        {"label": "Prediction leagues", "value": len(league_summary), "note": "covered"},
        {"label": "Result leagues", "value": len(history_summary), "note": "history"},
        {"label": "Signals", "value": len(ensemble_df), "note": "rows"},
        {"label": "Results", "value": len(history_df), "note": "rows"},
    ],
)

league_options = unique_options(ensemble_df, "League")
selected_league = st.selectbox("League detail", league_options)
detail_df = filter_by_column_value(ensemble_df, "League", selected_league)

kpi_grid([
    {"icon": "🌍", "title": "Selected", "value": selected_league, "sub": "league"},
    {"icon": "📈", "title": "Signals", "value": len(detail_df), "sub": "filtered"},
    {"icon": "📚", "title": "History rows", "value": len(history_df), "sub": "all leagues"},
])

left, right = st.columns(2, gap="large")
with left:
    section_title("Prediction coverage by league", "📈")
    dataframe_card(league_summary, height=360, limit=80, empty_title="No league prediction coverage")

with right:
    section_title("Historical coverage by league", "📚")
    dataframe_card(history_summary, height=360, limit=80, empty_title="No league history coverage")

section_title("Selected league signals", "▣")
compact_football_table(detail_df, limit=120)
