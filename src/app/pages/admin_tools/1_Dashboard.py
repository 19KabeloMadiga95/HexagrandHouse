from __future__ import annotations

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, dataframe_card
from src.app.utils.sqlite_runtime import (
    cached_table,
    count_rows,
    database_summary,
    latest_value,
    sort_by_best_date,
)

configure_page("Admin Dashboard", "⚙️")
refresh_chip()

summary = database_summary()
lottery_history = sort_by_best_date(cached_table("lottery_history"))
lottery_predictions = sort_by_best_date(cached_table("lottery_predictions"))
football_history = sort_by_best_date(cached_table("football_history"))
football_ensemble = sort_by_best_date(cached_table("football_ensemble_predictions"))
football_fixtures = sort_by_best_date(cached_table("football_fixtures"), ascending=True)

compact_header(
    "ADMIN DASHBOARD",
    "SQLite command view.",
    "Operational health, warehouse coverage and latest loaded intelligence from the SQLite database.",
    tags=["SQLite source", "Cloud-ready", "No runtime Excel"],
    metrics=[
        {"label": "Tables", "value": len(summary), "note": "available"},
        {"label": "Rows", "value": f"{int(summary['RowCount'].sum()):,}" if not summary.empty else "0", "note": "warehouse"},
        {"label": "Lottery", "value": count_rows("lottery_predictions"), "note": "predictions"},
        {"label": "Football", "value": count_rows("football_ensemble_predictions"), "note": "signals"},
    ],
)

kpi_grid([
    {"icon": "🗄️", "title": "Database", "value": "Online" if not summary.empty else "Offline", "sub": "SQLite warehouse"},
    {"icon": "🎲", "title": "Latest lottery", "value": latest_value(lottery_history, "DrawDate"), "sub": "newest draw"},
    {"icon": "⚽", "title": "Football rows", "value": f"{len(football_ensemble):,}", "sub": "ensemble predictions"},
    {"icon": "📅", "title": "Fixtures", "value": f"{len(football_fixtures):,}", "sub": "upcoming source"},
])

left, right = st.columns([1.15, 0.85], gap="large")

with left:
    section_title("Database tables", "▣")
    dataframe_card(summary, height=300, limit=100, empty_title="No database tables")

with right:
    section_title("Latest loaded records", "◎")
    latest_rows = {
        "Lottery result date": latest_value(lottery_history, "DrawDate"),
        "Lottery prediction run": latest_value(lottery_predictions, "GeneratedAt"),
        "Football match date": latest_value(football_history, "MatchDate"),
        "Football signal date": latest_value(football_ensemble, "GeneratedAt"),
    }
    st.dataframe(
        [{"Metric": k, "Value": v} for k, v in latest_rows.items()],
        use_container_width=True,
        hide_index=True,
        height=180,
    )

section_title("Recent lottery predictions", "🎯")
dataframe_card(lottery_predictions.head(25), height=260, limit=25, empty_title="No lottery predictions")
