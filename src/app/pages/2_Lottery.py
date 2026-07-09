from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.utils.sqlite_runtime import cached_table, sort_by_date, count_rows, latest_label
from src.app.components.website import (
    hero,
    mini_cards,
    section_label,
    lottery_ticket,
    lottery_result_group_card,
    empty_message,
    friendly_table,
    page_footer,
)

configure_page("Lottery Picks", "✤")
refresh_chip()

PRIMARY_GAME_OPTIONS = [
    "All",
    "Daily Lotto",
    "Lotto",
    "PowerBall",
    "UK49s Lunchtime",
    "UK49s Teatime",
]

RELATED_RESULT_ORDER = {
    "Daily Lotto": ["daily lotto"],
    "Lotto": ["lotto", "lotto plus 1", "lotto plus 2"],
    "PowerBall": ["powerball", "powerball plus"],
    "UK49s Lunchtime": ["uk49s lunchtime", "uk49s lunch time", "uk49s"],
    "UK49s Teatime": ["uk49s teatime", "uk49s tea time", "uk49s"],
}

RESULT_NUMBER_COLUMNS = ["N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]

PLUS_GAME_NAMES = {"lotto plus 1", "lotto plus 2", "powerball plus"}


def _norm(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip().lower()


def _game_name(row) -> str:
    return str(row.get("GameName", row.get("GameFamily", ""))).strip()


def _draw_type(row) -> str:
    return str(row.get("DrawType", "")).strip()


def lottery_game_group(row) -> str:
    game = _norm(_game_name(row))
    draw = _norm(_draw_type(row))

    if game in {"lotto", "lotto plus 1", "lotto plus 2"}:
        return "Lotto"
    if game in {"powerball", "powerball plus"}:
        return "PowerBall"
    if game == "daily lotto":
        return "Daily Lotto"
    if "uk49" in game:
        if "lunch" in game or "lunch" in draw:
            return "UK49s Lunchtime"
        if "tea" in game or "tea" in draw:
            return "UK49s Teatime"
        return "UK49s"

    return _game_name(row) or "Other"


def lottery_subgame_label(row) -> str:
    game = _game_name(row) or "Lottery"
    draw = _draw_type(row)

    if "uk49" in _norm(game) and draw:
        return f"UK49s {draw}".strip()
    return game


def clean_predictions(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    if "N1" in out.columns:
        out = out[pd.to_numeric(out["N1"], errors="coerce").notna()]

    if out.empty:
        return out

    if "GeneratedAt" in out.columns:
        out["_generated"] = pd.to_datetime(out["GeneratedAt"], errors="coerce")
    elif "EnsembleGeneratedAt" in out.columns:
        out["_generated"] = pd.to_datetime(out["EnsembleGeneratedAt"], errors="coerce")
    else:
        out["_generated"] = pd.NaT

    out["_rank"] = pd.to_numeric(out.get("PredictionRank", 999), errors="coerce")
    out["_score"] = pd.to_numeric(out.get("ConfidenceScore", out.get("RawScore", 0)), errors="coerce")
    out["GameGroup"] = out.apply(lottery_game_group, axis=1)

    if "GameName" in out.columns:
        out = out[~out["GameName"].astype(str).str.strip().str.lower().isin(PLUS_GAME_NAMES)]

    return out.sort_values(["_generated", "_rank", "_score"], ascending=[False, True, False], na_position="last")


def prepare_results(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = sort_by_date(df).copy()
    if "DrawDate" in out.columns:
        out["DrawDate"] = pd.to_datetime(out["DrawDate"], errors="coerce")
        out["DrawDay"] = out["DrawDate"].dt.date
    else:
        out["DrawDay"] = pd.NaT

    out["GameGroup"] = out.apply(lottery_game_group, axis=1)
    out["SubGameDisplay"] = out.apply(lottery_subgame_label, axis=1)
    out["_subgame_order"] = out.apply(_subgame_order, axis=1)
    return out.sort_values(["DrawDate", "GameGroup", "_subgame_order"], ascending=[False, True, True], na_position="last")


def _subgame_order(row) -> int:
    group = lottery_game_group(row)
    subgame = _norm(lottery_subgame_label(row))
    order = RELATED_RESULT_ORDER.get(group, [])
    try:
        return order.index(subgame)
    except ValueError:
        return 99


def filter_game_group(df: pd.DataFrame, selected_game: str) -> pd.DataFrame:
    if df is None or df.empty or selected_game in (None, "", "All"):
        return df
    if "GameGroup" not in df.columns:
        return df
    return df[df["GameGroup"].astype(str) == str(selected_game)]


def dedupe_lottery_result_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove repeated result rows while keeping the newest copy.

    The history table can contain duplicate draw rows after ingestion reruns.
    We dedupe by draw day + grouped game + subgame + numbers so grouped cards
    show Lotto/Lotto Plus 1/Lotto Plus 2 once per draw date.
    """
    if df is None or df.empty:
        return df

    out = df.copy()
    if "DrawDate" in out.columns:
        out["DrawDate"] = pd.to_datetime(out["DrawDate"], errors="coerce")
        out["DrawDay"] = out["DrawDate"].dt.date

    subset = [
        col
        for col in ["DrawDay", "GameGroup", "SubGameDisplay", "GameName", "DrawType", *RESULT_NUMBER_COLUMNS]
        if col in out.columns
    ]

    if not subset:
        return out

    out = out.sort_values("DrawDate", ascending=False, na_position="last") if "DrawDate" in out.columns else out
    return out.drop_duplicates(subset=subset, keep="first")


def grouped_recent_results(df: pd.DataFrame, limit: int = 5) -> list[pd.DataFrame]:
    if df is None or df.empty:
        return []

    work = df.copy()
    if "DrawDate" not in work.columns:
        return []

    work["DrawDate"] = pd.to_datetime(work["DrawDate"], errors="coerce")
    work = work[work["DrawDate"].notna()]
    if work.empty:
        return []

    work["DrawDay"] = work["DrawDate"].dt.date
    work = dedupe_lottery_result_rows(work)
    groups: list[tuple[pd.Timestamp, str, pd.DataFrame]] = []

    for (draw_day, game_group), group in work.groupby(["DrawDay", "GameGroup"], dropna=False):
        group = group.sort_values(["_subgame_order", "DrawDate"], ascending=[True, False], na_position="last")
        latest_date = pd.to_datetime(group["DrawDate"], errors="coerce").max()
        groups.append((latest_date, str(game_group), group))

    groups.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [group for _, _, group in groups[:limit]]


@st.cache_data(ttl=300, show_spinner=False)
def load_lottery():
    predictions = clean_predictions(cached_table("lottery_predictions", limit=800))
    results = prepare_results(cached_table("lottery_history", limit=1500))
    return predictions, results


predictions, results = load_lottery()
selected_game = st.radio("Choose a game", PRIMARY_GAME_OPTIONS, index=0, horizontal=True)

view_predictions = filter_game_group(predictions, selected_game)
view_results = filter_game_group(results, selected_game)
latest_result_groups = grouped_recent_results(view_results, limit=5)

hero(
    "Lottery Picks",
    "Data-driven lottery tickets based on statistical analysis, historical patterns, and grouped latest results.",
    eyebrow="Lottery intelligence",
    chips=[latest_label(results, "DrawDate", "GameName"), "Grouped Lotto results", "Current rules", "Entertainment only"],
    metrics=[
        {"value": len(PRIMARY_GAME_OPTIONS) - 1, "label": "Games covered"},
        {"value": f"{len(view_predictions):,}", "label": "Picks"},
        {"value": latest_label(results, "DrawDate", "GameName"), "label": "Latest draw"},
        {"value": "Ready", "label": "Status"},
    ],
)

mini_cards([
    {"icon": "🎟️", "label": "View", "value": selected_game, "note": "selected game"},
    {"icon": "🎲", "label": "Tickets", "value": f"{len(view_predictions):,}", "note": "available now"},
    {"icon": "📌", "label": "Latest", "value": latest_label(view_results, "DrawDate", "GameName"), "note": "newest draw"},
    {"icon": "🧾", "label": "History", "value": f"{count_rows('lottery_history'):,}", "note": "stored results"},
])

section_label("Featured Tickets", "Premium ticket cards for the selected game view.")
if view_predictions.empty:
    empty_message("No tickets available", "Try another game or wait for the next refresh.")
else:
    cols = st.columns(4, gap="medium")
    for i, (_, row) in enumerate(view_predictions.head(8).iterrows(), 1):
        with cols[(i - 1) % 4]:
            lottery_ticket(row, i)

section_label("Latest Results", "Last five grouped result cards for the selected game view.")
if not latest_result_groups:
    empty_message("No result history", "Results are not available for this game yet.")
else:
    cols = st.columns(2, gap="medium")
    for i, group in enumerate(latest_result_groups):
        with cols[i % 2]:
            lottery_result_group_card(group)

with st.expander("Show results table", expanded=False):
    friendly_table(
        view_results,
        ["DrawDate", "GameGroup", "SubGameDisplay", "GameName", "DrawType", "N1", "N2", "N3", "N4", "N5", "N6", "Bonus"],
        height=300,
        limit=100,
    )

page_footer()
