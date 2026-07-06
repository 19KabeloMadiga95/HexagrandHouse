from __future__ import annotations

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, football_card, compact_football_table, dataframe_card
from src.app.utils.sqlite_runtime import cached_table, filter_by_column_value, sort_by_best_date, sort_by_confidence, unique_options

configure_page("Fixture Predictions", "📅")
refresh_chip()

fixtures_df = sort_by_best_date(cached_table("football_fixtures"), ascending=True)
raw_predictions = sort_by_best_date(cached_table("football_predictions"))
ensemble_df = sort_by_confidence(cached_table("football_ensemble_predictions"))

prediction_source = raw_predictions if not raw_predictions.empty else ensemble_df
source_name = "football_predictions" if not raw_predictions.empty else "football_ensemble_predictions"

compact_header(
    "FIXTURE PREDICTIONS",
    "Fixture intelligence from SQLite.",
    "Upcoming fixture source and prediction signals are read from database tables.",
    tags=["Fixtures", "SQLite", source_name],
    metrics=[
        {"label": "Fixtures", "value": len(fixtures_df), "note": "rows"},
        {"label": "Predictions", "value": len(prediction_source), "note": "rows"},
        {"label": "Source", "value": source_name, "note": "table"},
    ],
)

league_options = unique_options(prediction_source, "League")
selected_league = st.selectbox("League", league_options)
view_df = filter_by_column_value(prediction_source, "League", selected_league)

kpi_grid([
    {"icon": "📅", "title": "Fixtures", "value": len(fixtures_df), "sub": "available"},
    {"icon": "⚽", "title": "Predictions", "value": len(view_df), "sub": "filtered"},
    {"icon": "🌍", "title": "Leagues", "value": prediction_source["League"].nunique() if "League" in prediction_source.columns else 0, "sub": "covered"},
])

left, right = st.columns([1.05, 0.95], gap="large")
with left:
    section_title("Fixture signals", "🔥")
    for rank, (_, row) in enumerate(view_df.head(10).iterrows(), start=1):
        football_card(row, rank=rank)

with right:
    section_title("Fixture source", "📅")
    dataframe_card(fixtures_df, height=420, limit=80, empty_title="No fixture rows")

section_title("Prediction table", "▣")
compact_football_table(view_df, limit=150)
