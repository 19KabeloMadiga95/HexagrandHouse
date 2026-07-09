from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.utils.sqlite_runtime import cached_table, count_rows, sort_by_date, sort_by_strength, latest_label
from src.app.components.website import (
    hero,
    mini_cards,
    section_label,
    lottery_ticket,
    football_pick,
    result_row,
    empty_message,
    page_footer,
)

configure_page("Home", "◆")
refresh_chip()


def current_football_only(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    date_col = next((c for c in ["FixtureDate", "MatchDate", "Date"] if c in out.columns), None)
    if date_col is None:
        return pd.DataFrame()
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
    today = pd.Timestamp.today().normalize()
    return out[out[date_col].notna() & (out[date_col] >= today)].copy()


def clean_lottery_predictions(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if "N1" in out.columns:
        out = out[pd.to_numeric(out["N1"], errors="coerce").notna()]
    if "GameName" in out.columns:
        out = out[out["GameName"].astype(str).str.lower().ne("football")]
    if "GeneratedAt" in out.columns:
        out["_generated"] = pd.to_datetime(out["GeneratedAt"], errors="coerce")
    elif "EnsembleGeneratedAt" in out.columns:
        out["_generated"] = pd.to_datetime(out["EnsembleGeneratedAt"], errors="coerce")
    else:
        out["_generated"] = pd.NaT
    out["_rank"] = pd.to_numeric(out.get("PredictionRank", 999), errors="coerce")
    return out.sort_values(["_generated", "_rank"], ascending=[False, True], na_position="last")


@st.cache_data(ttl=300, show_spinner=False)
def load_home():
    lottery_predictions = clean_lottery_predictions(cached_table("lottery_predictions", limit=600))
    lottery_results = sort_by_date(cached_table("lottery_history", limit=250))
    football_picks = sort_by_strength(current_football_only(cached_table("football_fixture_predictions", limit=500)))
    football_value = sort_by_strength(current_football_only(cached_table("football_value_bets", limit=500)))
    return lottery_predictions, lottery_results, football_picks, football_value


lottery_predictions, lottery_results, football_picks, football_value = load_home()

latest_draw = latest_label(lottery_results, "DrawDate", "GameName")
lottery_count = len(lottery_predictions)
football_count = len(football_picks)
result_count = count_rows("lottery_history") + count_rows("football_history")
league_count = football_picks["League"].nunique() if not football_picks.empty and "League" in football_picks.columns else 0

hero(
    "Smart Lottery & Football Insights",
    "Data-driven picks, grouped historical results, and football value intelligence in one clean public dashboard.",
    eyebrow="HexaGrandBet",
    chips=["All", "Lottery", "Football", "Results archive"],
    metrics=[
        {"value": "12", "label": "Games covered"},
        {"value": f"{lottery_count + football_count:,}", "label": "Active picks"},
        {"value": f"{result_count:,}", "label": "Historical results"},
        {"value": "Operational", "label": "Platform status"},
    ],
)

view = st.radio("Focus", ["All", "Lottery", "Football"], horizontal=True, label_visibility="collapsed")

mini_cards([
    {"icon": "✤", "label": "Lottery", "value": f"{lottery_count:,}", "note": "current tickets"},
    {"icon": "⚽", "label": "Football", "value": f"{football_count:,}", "note": f"{league_count} leagues"},
    {"icon": "▣", "label": "Latest draw", "value": latest_draw, "note": "updated daily"},
    {"icon": "✓", "label": "Status", "value": "Live", "note": "runtime database"},
])

if view in ["All", "Lottery"]:
    section_label("Featured Lottery Picks", "Top current tickets from the latest prediction run.")
    if lottery_predictions.empty:
        empty_message("No lottery picks yet", "The next refresh will populate this area.")
    else:
        cols = st.columns(3, gap="medium")
        for i, (_, row) in enumerate(lottery_predictions.head(6).iterrows(), 1):
            with cols[(i - 1) % 3]:
                lottery_ticket(row, i)

if view in ["All", "Football"]:
    section_label("Football Value Bets", "Current/future fixtures only. Historical football rows are never shown as live picks.")
    source = football_value if not football_value.empty else football_picks
    if source.empty:
        empty_message("No football picks yet", "Football cards will return when upcoming fixtures are available.")
    else:
        cols = st.columns(3, gap="medium")
        for i, (_, row) in enumerate(source.head(6).iterrows(), 1):
            with cols[(i - 1) % 3]:
                football_pick(row, i)

section_label("Latest Lottery Results", "Recent verified draw rows from the history table.")
if lottery_results.empty:
    empty_message("No results found", "Lottery results are not available yet.")
else:
    cols = st.columns(2, gap="medium")
    for i, (_, row) in enumerate(lottery_results.head(6).iterrows(), 1):
        with cols[(i - 1) % 2]:
            result_row(row)

section_label("Prediction Performance", "Lightweight summary view. Detailed model views are available in Insights.")
st.markdown(
    f"""
    <div class="hgb-card">
        <div class="hgb-progress-row"><div><b>Lottery Coverage</b><br/><span>{count_rows('lottery_history'):,} historical draw rows analysed</span></div><span class="hgb-pill">Updated</span></div>
        <div class="hgb-progress-row"><div><b>Football Safety Guard</b><br/><span>Public cards use current fixture predictions only</span></div><span class="hgb-pill">No stale picks</span></div>
        <div class="hgb-progress-row"><div><b>Responsible Play</b><br/><span>Insights are statistical reviews, not guarantees</span></div><span class="hgb-pill">18+</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

page_footer()
