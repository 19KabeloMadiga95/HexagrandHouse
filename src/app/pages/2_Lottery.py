from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, lottery_ticket, dataframe_card, empty_state, compact_lottery_table
from src.services.lottery_service import get_lottery_dashboard_data, filter_by_game, get_latest_results, get_result_coverage_summary

configure_page("Lottery Intelligence", "🎲")

@st.cache_data(ttl=300)
def load_data():
    return get_lottery_dashboard_data(limit=300)

d = load_data()
results_df = d.get("results_df", pd.DataFrame())
predictions_df = d.get("predictions_df", pd.DataFrame())
game_options = d.get("game_options", ["All"])
display_columns = d.get("display_columns", {})
k = d.get("kpis", {})
latest_draw = k.get("latest_draw", "-")
refresh_chip()

compact_header(
    "Lottery Intelligence",
    "Rules-aware tickets. Dense view.",
    "Curated predictions, recent draws and coverage without wasting screen space.",
    tags=[f"Latest: {latest_draw}", "Current rules active"],
    metrics=[
        {"label": "Games", "value": k.get("game_count", len(game_options)), "note": "tracked"},
        {"label": "Results", "value": k.get("result_count", len(results_df)), "note": "history"},
        {"label": "Predictions", "value": k.get("prediction_count", len(predictions_df)), "note": "curated"},
        {"label": "Status", "value": "Ready", "note": "rules-aware"},
    ],
)

selected_game = st.selectbox("Select game", game_options, index=0)
fp = filter_by_game(predictions_df, selected_game)
fr = filter_by_game(results_df, selected_game)
latest = get_latest_results(fr, limit=12)
coverage = get_result_coverage_summary(fr)

kpi_grid([
    {"title": "View", "value": selected_game, "sub": "selected game", "icon": "◆"},
    {"title": "Predictions", "value": len(fp), "sub": "generated selections", "icon": "◎"},
    {"title": "Results", "value": len(fr), "sub": "historical rows", "icon": "▤"},
    {"title": "Latest draw", "value": latest.iloc[0].get("DrawDate", "-") if not latest.empty else "-", "sub": "newest result", "icon": "◴"},
])

left, right = st.columns([1.05, .95], gap="medium")
with left:
    section_title("Featured tickets", "🎯")
    if fp.empty:
        empty_state("No predictions", "No prediction data is available for the selected game.")
    else:
        for i, (_, row) in enumerate(fp.head(10).iterrows(), 1):
            lottery_ticket(row, i)
with right:
    section_title("Latest results", "📌")
    compact_lottery_table(latest, kind="results", limit=12)
    section_title("Coverage", "▦")
    dataframe_card(coverage, height=170, limit=12, empty_title="No coverage summary")

with st.expander("Open prediction and result tables", expanded=False):
    tab1, tab2 = st.tabs(["Prediction table", "Result table"])
    with tab1:
        compact_lottery_table(fp, kind="predictions", limit=150)
    with tab2:
        compact_lottery_table(fr, kind="results", limit=150)
