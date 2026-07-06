from __future__ import annotations

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import (
    compact_header,
    kpi_grid,
    section_title,
    lottery_ticket,
    football_card,
    compact_lottery_table,
    compact_football_table,
)
from src.app.utils.sqlite_runtime import (
    cached_table,
    filter_by_column_value,
    sort_by_best_date,
    sort_by_confidence,
    unique_options,
    show_database_download,
)

configure_page("Predictions", "🎯")
refresh_chip()

lottery_df = sort_by_best_date(cached_table("lottery_predictions"))
football_df = sort_by_confidence(cached_table("football_ensemble_predictions"))

compact_header(
    "PREDICTION CENTRE",
    "All signals from SQLite.",
    "Lottery tickets and football signals now load from the SQLite warehouse, not Excel outputs.",
    tags=["SQLite", "Prediction layer", "Cloud-ready"],
    metrics=[
        {"label": "Lottery", "value": len(lottery_df), "note": "tickets"},
        {"label": "Football", "value": len(football_df), "note": "signals"},
    ],
)

mode = st.segmented_control(
    "Prediction type",
    ["Lottery", "Football"],
    default="Lottery",
)

if mode == "Lottery":
    game_options = unique_options(lottery_df, "GameName")
    selected_game = st.selectbox("Game", game_options)
    view_df = filter_by_column_value(lottery_df, "GameName", selected_game)

    kpi_grid([
        {"icon": "🎲", "title": "Selected", "value": selected_game, "sub": "game"},
        {"icon": "🎯", "title": "Tickets", "value": len(view_df), "sub": "filtered"},
        {"icon": "🗄️", "title": "Source", "value": "SQLite", "sub": "lottery_predictions"},
    ])

    section_title("Featured tickets", "🎯")
    for rank, (_, row) in enumerate(view_df.head(10).iterrows(), start=1):
        lottery_ticket(row, rank=rank)

    section_title("Prediction table", "▣")
    compact_lottery_table(view_df, kind="predictions", limit=100)
    show_database_download(view_df, "lottery_predictions.csv")

else:
    league_options = unique_options(football_df, "League")
    selected_league = st.selectbox("League", league_options)
    view_df = filter_by_column_value(football_df, "League", selected_league)

    kpi_grid([
        {"icon": "⚽", "title": "Selected", "value": selected_league, "sub": "league"},
        {"icon": "📈", "title": "Signals", "value": len(view_df), "sub": "filtered"},
        {"icon": "🗄️", "title": "Source", "value": "SQLite", "sub": "football_ensemble_predictions"},
    ])

    section_title("Top football signals", "🔥")
    for rank, (_, row) in enumerate(view_df.head(10).iterrows(), start=1):
        football_card(row, rank=rank)

    section_title("Prediction table", "▣")
    compact_football_table(view_df, limit=120)
    show_database_download(view_df, "football_predictions.csv")
