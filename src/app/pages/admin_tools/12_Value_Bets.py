from __future__ import annotations

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, football_card, compact_football_table, dataframe_card
from src.app.utils.sqlite_runtime import cached_table, filter_by_column_value, sort_by_confidence, unique_options, show_database_download

configure_page("Value Bets", "💎")
refresh_chip()

football_df = sort_by_confidence(cached_table("football_ensemble_predictions"))

if not football_df.empty:
    value_df = football_df.copy()
    for confidence_col in ["ConfidenceScore", "EnsembleConfidenceScore", "Confidence"]:
        if confidence_col in value_df.columns:
            value_df[confidence_col] = pd.to_numeric(value_df[confidence_col], errors="coerce")
            value_df = value_df.sort_values(confidence_col, ascending=False, na_position="last")
            break
else:
    value_df = pd.DataFrame()

compact_header(
    "VALUE SIGNALS",
    "Market edges from SQLite.",
    "This is a database-first proxy view using the highest-confidence football ensemble signals until odds tables are migrated.",
    tags=["Value", "Football", "SQLite"],
    metrics=[
        {"label": "Value rows", "value": len(value_df), "note": "signals"},
        {"label": "Leagues", "value": value_df["League"].nunique() if "League" in value_df.columns else 0, "note": "covered"},
    ],
)

league_options = unique_options(value_df, "League")
selected_league = st.selectbox("League", league_options)
view_df = filter_by_column_value(value_df, "League", selected_league)

kpi_grid([
    {"icon": "💎", "title": "Value signals", "value": len(view_df), "sub": "filtered"},
    {"icon": "⚽", "title": "Source", "value": "Ensemble", "sub": "SQLite table"},
    {"icon": "🌍", "title": "League", "value": selected_league, "sub": "selected"},
])

left, right = st.columns([1.05, 0.95], gap="large")
with left:
    section_title("Value signal cards", "💎")
    for rank, (_, row) in enumerate(view_df.head(12).iterrows(), start=1):
        football_card(row, rank=rank)

with right:
    section_title("Value distribution", "📊")
    if not view_df.empty and "ConfidenceLabel" in view_df.columns:
        summary = view_df.groupby("ConfidenceLabel", dropna=False).size().reset_index(name="Count")
        dataframe_card(summary, height=260, limit=50, empty_title="No value distribution")
    else:
        dataframe_card(pd.DataFrame(), height=260, limit=50, empty_title="No value distribution")

section_title("Value signals table", "▣")
compact_football_table(view_df, limit=150)
show_database_download(view_df, "value_signals.csv")
