from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.utils.sqlite_runtime import cached_table, count_rows, sort_by_date, sort_by_strength, latest_label
from src.app.components.website import hero, mini_cards, section_label, lottery_ticket, football_pick, result_row, empty_message, page_footer

configure_page("Home", "🏠")
refresh_chip()


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
    if "PredictionRank" in out.columns:
        out["_rank"] = pd.to_numeric(out["PredictionRank"], errors="coerce")
    else:
        out["_rank"] = 999
    return out.sort_values(["_generated", "_rank"], ascending=[False, True], na_position="last")


@st.cache_data(ttl=300, show_spinner=False)
def load_home():
    lottery_predictions = clean_lottery_predictions(cached_table("lottery_predictions", limit=400))
    lottery_results = sort_by_date(cached_table("lottery_history", limit=200))
    football_picks = sort_by_strength(cached_table("football_top_plays", limit=500))
    if football_picks.empty:
        football_picks = sort_by_strength(cached_table("football_predictions", limit=500))
    football_value = sort_by_strength(cached_table("football_value_bets", limit=500))
    return lottery_predictions, lottery_results, football_picks, football_value

lottery_predictions, lottery_results, football_picks, football_value = load_home()

latest_draw = latest_label(lottery_results, "DrawDate", "GameName")
lottery_count = count_rows("lottery_predictions")
football_count = count_rows("football_top_plays") or count_rows("football_predictions")
result_count = count_rows("lottery_history") + count_rows("football_history")

hero(
    "Simple picks. Clear results.",
    "A clean home for lottery numbers, football picks and recent outcomes. No spreadsheets. No heavy dashboards. Just the latest selections.",
    eyebrow="Welcome",
    chips=["Lottery", "Football", "Results", "Play smart"],
    metrics=[
        {"value": f"{lottery_count:,}", "label": "Lottery picks"},
        {"value": f"{football_count:,}", "label": "Football picks"},
        {"value": latest_draw, "label": "Latest draw"},
        {"value": f"{result_count:,}", "label": "Results"},
    ],
)

mini_cards([
    {"icon": "🎲", "label": "Lottery", "value": f"{lottery_count:,}", "note": "fresh selections"},
    {"icon": "⚽", "label": "Football", "value": f"{football_count:,}", "note": "top picks"},
    {"icon": "📋", "label": "Results", "value": f"{result_count:,}", "note": "recent outcomes"},
    {"icon": "🛡️", "label": "Reminder", "value": "Play smart", "note": "optional only"},
])

left, right = st.columns([1, 1], gap="medium")

with left:
    section_label("Today’s lottery picks", "Latest available selections.")
    if lottery_predictions.empty:
        empty_message("No lottery picks yet", "The next refresh will populate this area.")
    else:
        for i, (_, row) in enumerate(lottery_predictions.head(4).iterrows(), 1):
            lottery_ticket(row, i)

with right:
    section_label("Football picks", "Top matches to review.")
    if football_picks.empty:
        empty_message("No football picks yet", "The football list will populate once match data is available.")
    else:
        for i, (_, row) in enumerate(football_picks.head(4).iterrows(), 1):
            football_pick(row, i)

section_label("Latest lottery results", "Recent draws in a simple card view.")
if lottery_results.empty:
    empty_message("No results found", "Lottery results are not available yet.")
else:
    for _, row in lottery_results.head(4).iterrows():
        result_row(row)

page_footer()
