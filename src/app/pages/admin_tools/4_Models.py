from __future__ import annotations

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, dataframe_card
from src.app.utils.sqlite_runtime import cached_table, database_summary, sort_by_best_date, sort_by_confidence

configure_page("Models", "🧠")
refresh_chip()

summary = database_summary()
lottery_predictions = sort_by_best_date(cached_table("lottery_predictions"))
football_predictions = sort_by_confidence(cached_table("football_ensemble_predictions"))
football_backtest = sort_by_best_date(cached_table("football_backtest_history"))

compact_header(
    "MODEL INTELLIGENCE",
    "Model outputs without Excel files.",
    "This page reads model-ready outputs from SQLite and surfaces coverage, latest runs and available warehouse tables.",
    tags=["Model layer", "SQLite", "No Excel runtime"],
    metrics=[
        {"label": "Lottery outputs", "value": len(lottery_predictions), "note": "rows"},
        {"label": "Football outputs", "value": len(football_predictions), "note": "rows"},
        {"label": "Backtest rows", "value": len(football_backtest), "note": "history"},
        {"label": "Tables", "value": len(summary), "note": "warehouse"},
    ],
)

kpi_grid([
    {"icon": "🎲", "title": "Lottery models", "value": lottery_predictions["ModelName"].nunique() if "ModelName" in lottery_predictions.columns else "-", "sub": "model names"},
    {"icon": "⚽", "title": "Football leagues", "value": football_predictions["League"].nunique() if "League" in football_predictions.columns else "-", "sub": "coverage"},
    {"icon": "📊", "title": "Confidence rows", "value": len(football_predictions), "sub": "ensemble"},
    {"icon": "🗄️", "title": "Runtime source", "value": "SQLite", "sub": "single warehouse"},
])

left, right = st.columns(2, gap="large")
with left:
    section_title("Lottery model outputs", "🎲")
    dataframe_card(lottery_predictions, height=330, limit=50, empty_title="No lottery model outputs")

with right:
    section_title("Football model outputs", "⚽")
    dataframe_card(football_predictions, height=330, limit=50, empty_title="No football model outputs")

section_title("Warehouse inventory", "▣")
dataframe_card(summary, height=260, limit=100, empty_title="No database inventory")
