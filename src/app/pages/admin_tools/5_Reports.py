from __future__ import annotations

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, dataframe_card
from src.app.utils.sqlite_runtime import available_tables, cached_table, database_summary, show_database_download

configure_page("Reports", "📄")
refresh_chip()

summary = database_summary()
tables = available_tables()

compact_header(
    "REPORT CENTRE",
    "SQLite reports on demand.",
    "Excel is no longer used as the runtime report source. Reports are built from database tables and can be exported when needed.",
    tags=["SQLite reporting", "CSV export", "Cloud-ready"],
    metrics=[
        {"label": "Tables", "value": len(tables), "note": "available"},
        {"label": "Rows", "value": f"{int(summary['RowCount'].sum()):,}" if not summary.empty else "0", "note": "warehouse"},
    ],
)

kpi_grid([
    {"icon": "🎲", "title": "Lottery history", "value": int(summary.loc[summary.TableName.eq("lottery_history"), "RowCount"].sum()) if not summary.empty else 0, "sub": "rows"},
    {"icon": "🎯", "title": "Lottery predictions", "value": int(summary.loc[summary.TableName.eq("lottery_predictions"), "RowCount"].sum()) if not summary.empty else 0, "sub": "rows"},
    {"icon": "⚽", "title": "Football history", "value": int(summary.loc[summary.TableName.eq("football_history"), "RowCount"].sum()) if not summary.empty else 0, "sub": "rows"},
    {"icon": "📈", "title": "Football signals", "value": int(summary.loc[summary.TableName.eq("football_ensemble_predictions"), "RowCount"].sum()) if not summary.empty else 0, "sub": "rows"},
])

selected_table = st.selectbox("Select report table", tables if tables else ["No tables"])
if selected_table and selected_table != "No tables":
    df = cached_table(selected_table)
    section_title(f"Report preview: {selected_table}", "▣")
    dataframe_card(df, height=420, limit=100, empty_title="No report rows")
    show_database_download(df, f"{selected_table}.csv", label=f"Download {selected_table} CSV")

section_title("Database summary", "🗄️")
dataframe_card(summary, height=260, limit=100, empty_title="No database summary")
