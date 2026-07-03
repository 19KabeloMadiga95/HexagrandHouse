from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, lottery_ticket, football_card, dataframe_card
from src.services.home_service import get_home_dashboard_data

configure_page("Command Centre", "⬢")

@st.cache_data(ttl=300)
def load_data():
    return get_home_dashboard_data()

d = load_data()
refresh_chip(value=d.get("platform_health", {}).get("last_refresh") or None)

compact_header(
    "Command Centre",
    "One workspace. Fast signals.",
    "Lottery picks, football edges, latest outcomes and platform health in one compact intelligence view.",
    tags=[f"Status: {d.get('platform_status','-')}", "Autonomous daily cycle", "Rules-aware lottery"],
    metrics=[
        {"label": "Rows", "value": f"{d.get('total_rows', 0):,}", "note": "records"},
        {"label": "Football", "value": d.get("football_results_count", "-"), "note": "results"},
        {"label": "Lottery", "value": d.get("latest_lottery_result", "-"), "note": "latest"},
        {"label": "Accuracy", "value": d.get("model_accuracy", "-"), "note": "tracking"},
    ],
)

kpi_grid([
    {"title": "Platform", "value": d.get("platform_status", "-"), "sub": "Database and services", "icon": "●"},
    {"title": "Rows", "value": f"{d.get('total_rows', 0):,}", "sub": "Warehouse records", "icon": "▦"},
    {"title": "Latest lottery", "value": d.get("latest_lottery_result", "-"), "sub": "Most recent draw", "icon": "🎲"},
    {"title": "Top football", "value": d.get("top_play", "-"), "sub": "Current signal", "icon": "⚽"},
])

left, right = st.columns([1.05, .95], gap="medium")
with left:
    section_title("Today’s lottery signal", "🎲")
    pred = d.get("predictions_df", pd.DataFrame())
    if pred is not None and not pred.empty:
        lottery_ticket(pred.iloc[0], 1)
    else:
        st.info("No lottery prediction available yet.")
with right:
    section_title("Football signal", "⚽")
    st.markdown(
        f'<div class="hgh-panel"><div class="hgh-panel-title">Top play</div><p class="hgh-panel-sub">{d.get("top_play", "-")}</p>'
        f'<div class="hgh-panel-title">Value signal</div><p class="hgh-panel-sub">{d.get("top_value_signal", "-")}</p></div>',
        unsafe_allow_html=True,
    )

section_title("Database snapshot", "▦")
dataframe_card(d.get("db_summary_df", pd.DataFrame()), height=220, limit=12, empty_title="Database summary unavailable")
