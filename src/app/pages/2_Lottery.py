from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.utils.sqlite_runtime import cached_table, sort_by_date, unique_options, filter_value, count_rows, latest_label
from src.app.components.website import hero, mini_cards, section_label, lottery_ticket, result_row, empty_message, friendly_table, page_footer

configure_page("Lottery Picks", "🎲")
refresh_chip()


def clean_predictions(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if "N1" in out.columns:
        out = out[pd.to_numeric(out["N1"], errors="coerce").notna()]
    if "GeneratedAt" in out.columns:
        out["_generated"] = pd.to_datetime(out["GeneratedAt"], errors="coerce")
    elif "EnsembleGeneratedAt" in out.columns:
        out["_generated"] = pd.to_datetime(out["EnsembleGeneratedAt"], errors="coerce")
    else:
        out["_generated"] = pd.NaT
    out["_rank"] = pd.to_numeric(out.get("PredictionRank", 999), errors="coerce")
    out["_score"] = pd.to_numeric(out.get("ConfidenceScore", out.get("RawScore", 0)), errors="coerce")
    return out.sort_values(["_generated", "_rank", "_score"], ascending=[False, True, False], na_position="last")


@st.cache_data(ttl=300, show_spinner=False)
def load_lottery():
    predictions = clean_predictions(cached_table("lottery_predictions", limit=500))
    results = sort_by_date(cached_table("lottery_history", limit=500))
    return predictions, results

predictions, results = load_lottery()
games = unique_options(predictions if not predictions.empty else results, "GameName")
selected_game = st.selectbox("Choose a game", games, index=0)

view_predictions = filter_value(predictions, "GameName", selected_game)
view_results = filter_value(results, "GameName", selected_game)

hero(
    "Lottery picks.",
    "Numbers are shown like tickets, with recent draws beside them. Choose a game and review the latest selections.",
    eyebrow="Lottery",
    chips=[latest_label(results, "DrawDate", "GameName"), "Current rules", "Entertainment only"],
    metrics=[
        {"value": len(games) - 1 if games and games[0] == "All" else len(games), "label": "Games"},
        {"value": f"{len(view_predictions):,}", "label": "Picks"},
        {"value": f"{len(view_results):,}", "label": "Results"},
        {"value": "Ready", "label": "Status"},
    ],
)

mini_cards([
    {"icon": "🎟️", "label": "View", "value": selected_game, "note": "selected game"},
    {"icon": "🎲", "label": "Tickets", "value": f"{len(view_predictions):,}", "note": "available now"},
    {"icon": "📌", "label": "Latest", "value": latest_label(view_results, "DrawDate", "GameName"), "note": "newest draw"},
    {"icon": "🧾", "label": "History", "value": f"{count_rows('lottery_history'):,}", "note": "stored results"},
])

left, right = st.columns([1, 1], gap="medium")

with left:
    section_label("Featured tickets", "First ten tickets for this view.")
    if view_predictions.empty:
        empty_message("No tickets available", "Try another game or wait for the next refresh.")
    else:
        for i, (_, row) in enumerate(view_predictions.head(10).iterrows(), 1):
            lottery_ticket(row, i)

with right:
    section_label("Latest results", "Recent draws for the selected game.")
    if view_results.empty:
        empty_message("No result history", "Results are not available for this game yet.")
    else:
        for _, row in view_results.head(8).iterrows():
            result_row(row)

with st.expander("Show results table", expanded=False):
    friendly_table(view_results, ["DrawDate", "GameName", "DrawType", "N1", "N2", "N3", "N4", "N5", "N6", "Bonus"], height=300, limit=100)

page_footer()
