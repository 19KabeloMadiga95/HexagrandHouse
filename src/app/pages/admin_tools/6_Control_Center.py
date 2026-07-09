from __future__ import annotations

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, dataframe_card, empty_state
from src.app.utils.sqlite_runtime import available_tables, cached_table, database_summary

configure_page("Control Center", "🕹️")
refresh_chip()

summary = database_summary()
tables = available_tables()

compact_header(
    "CONTROL CENTRE",
    "Database-first operations.",
    "Cloud-safe controls for inspecting warehouse state. Heavy pipelines should run outside the Streamlit request cycle.",
    tags=["SQLite", "Read-only cloud", "Operational view"],
    metrics=[
        {"label": "Status", "value": "Online" if tables else "Offline", "note": "database"},
        {"label": "Tables", "value": len(tables), "note": "available"},
        {"label": "Rows", "value": f"{int(summary['RowCount'].sum()):,}" if not summary.empty else "0", "note": "warehouse"},
    ],
)

kpi_grid([
    {"icon": "🗄️", "title": "Runtime source", "value": "SQLite", "sub": "runtime SQLite DB"},
    {"icon": "☁️", "title": "Cloud mode", "value": "Read-only", "sub": "safe deployment"},
    {"icon": "📦", "title": "Exports", "value": "Optional", "sub": "not runtime"},
    {"icon": "🧭", "title": "Architecture", "value": "v4", "sub": "database-first"},
])

left, right = st.columns([0.8, 1.2], gap="large")
with left:
    section_title("Actions", "⚙️")
    if st.button("Refresh cached data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.info("Pipeline execution is intentionally not triggered from Streamlit Cloud. Run automation externally, update SQLite, then redeploy or sync the database.")

with right:
    section_title("Warehouse status", "▣")
    dataframe_card(summary, height=300, limit=100, empty_title="No warehouse status")

section_title("Table preview", "🔎")
if tables:
    selected = st.selectbox("Choose table", tables)
    dataframe_card(cached_table(selected), height=360, limit=100, empty_title="Selected table is empty")
else:
    empty_state("No tables found", "The SQLite database has not been loaded.")
