from __future__ import annotations

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, dataframe_card, compact_football_table
from src.app.utils.sqlite_runtime import cached_table, sort_by_best_date, sort_by_confidence

configure_page("Model Performance", "📊")
refresh_chip()

backtest_df = sort_by_best_date(cached_table("football_backtest_history"))
football_df = sort_by_confidence(cached_table("football_ensemble_predictions"))
lottery_df = sort_by_best_date(cached_table("lottery_predictions"))

if not football_df.empty and "ConfidenceLabel" in football_df.columns:
    confidence_summary = (
        football_df.groupby("ConfidenceLabel", dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )
else:
    confidence_summary = pd.DataFrame(columns=["ConfidenceLabel", "Count"])

compact_header(
    "MODEL PERFORMANCE",
    "Performance-ready SQLite view.",
    "Backtest history, confidence labels and model output volume are read from database tables.",
    tags=["Performance", "SQLite", "No Excel dashboard files"],
    metrics=[
        {"label": "Backtest", "value": len(backtest_df), "note": "rows"},
        {"label": "Football", "value": len(football_df), "note": "signals"},
        {"label": "Lottery", "value": len(lottery_df), "note": "tickets"},
        {"label": "Labels", "value": len(confidence_summary), "note": "confidence"},
    ],
)

kpi_grid([
    {"icon": "📊", "title": "Backtest rows", "value": len(backtest_df), "sub": "football_backtest_history"},
    {"icon": "⭐", "title": "Confidence labels", "value": len(confidence_summary), "sub": "football ensemble"},
    {"icon": "🎲", "title": "Lottery outputs", "value": len(lottery_df), "sub": "prediction rows"},
    {"icon": "🗄️", "title": "Source", "value": "SQLite", "sub": "warehouse"},
])

left, right = st.columns(2, gap="large")
with left:
    section_title("Confidence distribution", "⭐")
    dataframe_card(confidence_summary, height=300, limit=50, empty_title="No confidence labels")

with right:
    section_title("Backtest history", "📚")
    dataframe_card(backtest_df, height=300, limit=50, empty_title="No backtest history")

section_title("Football model signals", "⚽")
compact_football_table(football_df, limit=120)
