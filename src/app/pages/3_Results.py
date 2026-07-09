from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.utils.sqlite_runtime import cached_table, sort_by_date, count_rows, latest_label
from src.app.components.website import (
    hero,
    mini_cards,
    section_label,
    lottery_result_group_card,
    empty_message,
    friendly_table,
    page_footer,
)

configure_page("Results", "📋")
refresh_chip()

GAME_FILTER_OPTIONS = [
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


def _subgame_order(row) -> int:
    group = lottery_game_group(row)
    subgame = _norm(lottery_subgame_label(row))
    order = RELATED_RESULT_ORDER.get(group, [])
    try:
        return order.index(subgame)
    except ValueError:
        return 99


def prepare_lottery_results(df: pd.DataFrame) -> pd.DataFrame:
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


def filter_game_group(df: pd.DataFrame, selected_game: str) -> pd.DataFrame:
    if df is None or df.empty or selected_game in (None, "", "All"):
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


def filter_date_range(df: pd.DataFrame, selected_dates) -> pd.DataFrame:
    if df is None or df.empty or "DrawDate" not in df.columns:
        return df

    if not selected_dates:
        return df

    if isinstance(selected_dates, tuple):
        if len(selected_dates) == 0:
            return df
        start = selected_dates[0]
        end = selected_dates[-1] if len(selected_dates) > 1 else selected_dates[0]
    else:
        start = selected_dates
        end = selected_dates

    if start is None or end is None:
        return df

    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    return df[(df["DrawDate"] >= start_ts) & (df["DrawDate"] <= end_ts)]


def grouped_lottery_results(df: pd.DataFrame, limit: int) -> list[pd.DataFrame]:
    if df is None or df.empty:
        return []

    work = df.copy()
    work["DrawDate"] = pd.to_datetime(work["DrawDate"], errors="coerce")
    work = work[work["DrawDate"].notna()]
    if work.empty:
        return []

    work["DrawDay"] = work["DrawDate"].dt.date
    work = dedupe_lottery_result_rows(work)
    groups: list[tuple[pd.Timestamp, str, pd.DataFrame]] = []

    for (draw_day, game_group), group in work.groupby(["DrawDay", "GameGroup"], dropna=False):
        group = group.sort_values(["_subgame_order", "DrawDate"], ascending=[True, False], na_position="last")
        groups.append((group["DrawDate"].max(), str(game_group), group))

    groups.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [group for _, _, group in groups[:limit]]


def _date_bounds(df: pd.DataFrame) -> tuple[date | None, date | None]:
    if df is None or df.empty or "DrawDate" not in df.columns:
        return None, None
    dates = pd.to_datetime(df["DrawDate"], errors="coerce").dropna()
    if dates.empty:
        return None, None

    latest = dates.max().date()
    earliest_allowed = latest - timedelta(days=365)
    available_min = dates.min().date()
    return max(available_min, earliest_allowed), latest


@st.cache_data(ttl=300, show_spinner=False)
def load_results():
    lottery = prepare_lottery_results(cached_table("lottery_history", limit=20000))
    football = sort_by_date(cached_table("football_history", limit=500))
    scored = sort_by_date(cached_table("football_backtest_history", limit=5000))
    return lottery, football, scored


lottery, football, scored = load_results()

hero(
    "Recent results.",
    "A clean historical view for lottery draws and football outcomes without opening spreadsheets.",
    eyebrow="Results",
    chips=["Historical draws", "Grouped results", "Simple filters"],
    metrics=[
        {"value": f"{count_rows('lottery_history'):,}", "label": "Lottery results"},
        {"value": f"{count_rows('football_history'):,}", "label": "Football results"},
        {"value": f"{len(scored):,}", "label": "Scored picks"},
        {"value": latest_label(lottery, "DrawDate", "GameName"), "label": "Latest draw"},
    ],
)

mini_cards([
    {"icon": "🎲", "label": "Lottery results", "value": f"{count_rows('lottery_history'):,}", "note": "total stored"},
    {"icon": "⚽", "label": "Football results", "value": f"{count_rows('football_history'):,}", "note": "total stored"},
    {"icon": "📌", "label": "Latest draw", "value": latest_label(lottery, "DrawDate", "GameName"), "note": "newest result"},
    {"icon": "🧾", "label": "Scored picks", "value": f"{count_rows('football_backtest_history'):,}", "note": "runtime sample"},
])

min_date, max_date = _date_bounds(lottery)

filter_cols = st.columns([1.15, 1, 1.35], gap="medium")
with filter_cols[0]:
    selected_game = st.selectbox("Lottery game", GAME_FILTER_OPTIONS, index=0)
with filter_cols[1]:
    last_n = st.selectbox("Last results", list(range(5, 55, 5)), index=0)
with filter_cols[2]:
    if min_date and max_date:
        selected_dates = st.date_input(
            "Draw date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
    else:
        selected_dates = None

lottery_view = filter_game_group(lottery, selected_game)
lottery_view = filter_date_range(lottery_view, selected_dates)
lottery_groups = grouped_lottery_results(lottery_view, limit=int(last_n))

left, right = st.columns([1.05, .95], gap="large")

with left:
    section_label("Lottery results", f"Last {last_n} grouped result cards for {selected_game}.")
    if not lottery_groups:
        empty_message("No lottery results", "No draws match the selected filters.")
    else:
        for group in lottery_groups:
            lottery_result_group_card(group)

with right:
    section_label("Football results", "Recent football rows in a simple table.")
    friendly_table(
        football,
        ["MatchDate", "Season", "League", "HomeTeam", "AwayTeam", "HomeGoals", "AwayGoals", "Result"],
        height=560,
        limit=80,
    )

with st.expander("Show filtered lottery table", expanded=False):
    friendly_table(
        lottery_view,
        ["DrawDate", "GameGroup", "SubGameDisplay", "GameName", "DrawType", "N1", "N2", "N3", "N4", "N5", "N6", "Bonus"],
        height=360,
        limit=250,
    )

page_footer()
