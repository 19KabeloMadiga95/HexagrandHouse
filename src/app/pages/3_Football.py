from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header, kpi_grid, section_title, football_card, dataframe_card, empty_state, compact_football_table
from src.services.football_service import get_football_dashboard_data, filter_by_league, filter_elite_only

configure_page("Football Intelligence", "⚽")

@st.cache_data(ttl=300)
def load_data():
    return get_football_dashboard_data(limit=500)

d = load_data()
k = d.get("kpis", {})
refresh_chip()
compact_header(
    "Football Intelligence",
    "Elite signals. Compact workspace.",
    "Top plays, value opportunities, coverage and source status in one dense view.",
    tags=[f"{k.get('leagues',0)} tracked competitions", "Source-aware fixtures"],
    metrics=[
        {"label": "Fixtures", "value": k.get("fixtures", 0), "note": "upcoming"},
        {"label": "Predictions", "value": k.get("predictions", 0), "note": "modelled"},
        {"label": "Leagues", "value": k.get("leagues", 0), "note": "tracked"},
        {"label": "Confidence", "value": k.get("average_confidence", "-"), "note": "avg"},
    ],
)

f1, f2 = st.columns(2)
with f1:
    league = st.selectbox("League", d.get("league_options", ["All"]))
with f2:
    confidence = st.selectbox("Confidence", ["All", "Elite Only"], index=0)

fixtures = filter_by_league(d.get("fixtures_df", pd.DataFrame()), league)
predictions = filter_by_league(d.get("predictions_df", pd.DataFrame()), league)
top = filter_by_league(d.get("top_predictions_df", pd.DataFrame()), league)
value = filter_by_league(d.get("value_bets_df", pd.DataFrame()), league)
summary = filter_by_league(d.get("league_summary_df", pd.DataFrame()), league)
if confidence == "Elite Only":
    predictions = filter_elite_only(predictions)
    top = filter_elite_only(top)
    value = filter_elite_only(value)

kpi_grid([
    {"title": "Fixtures", "value": len(fixtures), "sub": "selected view", "icon": "◴"},
    {"title": "Predictions", "value": len(predictions), "sub": "filtered rows", "icon": "◎"},
    {"title": "Top plays", "value": len(top), "sub": "shortlist", "icon": "★"},
    {"title": "Value bets", "value": len(value), "sub": "market edges", "icon": "◆"},
])

left, right = st.columns([1.05, .95], gap="medium")
with left:
    section_title("Match tickets", "🔥")
    card_df = top if not top.empty else predictions
    if card_df.empty:
        empty_state("No prediction cards", "No football prediction cards are available yet.")
    else:
        for i, (_, row) in enumerate(card_df.head(5).iterrows(), 1):
            football_card(row, i)
with right:
    section_title("Fixture source", "📅")
    if fixtures.empty:
        empty_state("No upcoming fixtures", "The current public source has no future fixtures. Archive predictions remain available.", "📡")
    else:
        cols = [c for c in d.get("display_columns", {}).get("fixtures", []) if c in fixtures.columns]
        dataframe_card(fixtures[cols] if cols else fixtures, height=220, limit=20)
    section_title("League coverage", "🌍")
    dataframe_card(summary, height=260, limit=25, empty_title="No league coverage")

with st.expander("Open value and prediction tables", expanded=False):
    tab1, tab2 = st.tabs(["Value opportunities", "Prediction table"])
    with tab1:
        compact_football_table(value, limit=120)
    with tab2:
        compact_football_table(predictions, limit=150)
