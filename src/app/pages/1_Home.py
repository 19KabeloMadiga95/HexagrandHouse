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
    lottery_ticket_markup,
    football_pick_markup,
    result_row_markup,
    cards_grid,
    empty_message,
    page_footer,
)

configure_page("Home", "◆")
refresh_chip()

LOTTERY_DISPLAY_ORDER = [
    "PowerBall",
    "Lotto",
    "Daily Lotto",
    "UK49s Lunchtime",
    "UK49s Teatime",
]


# -----------------------------
# Data cleanup helpers
# -----------------------------

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


def _norm(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip().lower()


def _lottery_group(row) -> str:
    game = _norm(row.get("GameName", row.get("GameFamily", "")))
    draw = _norm(row.get("DrawType", ""))

    if "powerball" in game:
        return "PowerBall"
    if game in {"lotto", "lotto plus 1", "lotto plus 2"}:
        return "Lotto"
    if "daily lotto" in game:
        return "Daily Lotto"
    if "uk49" in game:
        if "lunch" in game or "lunch" in draw:
            return "UK49s Lunchtime"
        if "tea" in game or "tea" in draw:
            return "UK49s Teatime"
        return "UK49s"

    return str(row.get("GameName", row.get("GameFamily", "Other"))).strip() or "Other"


def _first_numeric_column(df: pd.DataFrame, candidates: list[str], default: float = 0.0) -> pd.Series:
    for col in candidates:
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce").fillna(default)
    return pd.Series([default] * len(df), index=df.index)


def clean_lottery_predictions(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    if "N1" in out.columns:
        out = out[pd.to_numeric(out["N1"], errors="coerce").notna()]
    if "GameName" in out.columns:
        out = out[out["GameName"].astype(str).str.lower().ne("football")]

    if out.empty:
        return out

    if "GeneratedAt" in out.columns:
        out["_generated"] = pd.to_datetime(out["GeneratedAt"], errors="coerce")
    elif "EnsembleGeneratedAt" in out.columns:
        out["_generated"] = pd.to_datetime(out["EnsembleGeneratedAt"], errors="coerce")
    else:
        out["_generated"] = pd.NaT

    out["_rank"] = pd.to_numeric(out.get("PredictionRank", 999), errors="coerce").fillna(999)
    out["_score"] = _first_numeric_column(out, ["ConfidenceScore", "EnsembleConfidenceScore", "RawScore", "Score"])
    out["_game_group"] = out.apply(_lottery_group, axis=1)

    return out.sort_values(
        ["_generated", "_rank", "_score"],
        ascending=[False, True, False],
        na_position="last",
    )


def diverse_lottery_predictions(df: pd.DataFrame, limit: int = 6) -> pd.DataFrame:
    """Pick a balanced homepage sample instead of letting one daily game dominate."""
    if df is None or df.empty:
        return pd.DataFrame()

    work = df.copy()
    if "_game_group" not in work.columns:
        work["_game_group"] = work.apply(_lottery_group, axis=1)

    selected_indices: list[int] = []

    # First pass: one strong ticket per main game family.
    for game in LOTTERY_DISPLAY_ORDER:
        group = work[work["_game_group"] == game]
        if not group.empty:
            selected_indices.append(group.index[0])
        if len(selected_indices) >= limit:
            break

    # Second pass: fill remaining spaces using the next best tickets not already selected.
    for idx in work.index:
        if idx not in selected_indices:
            selected_indices.append(idx)
        if len(selected_indices) >= limit:
            break

    return work.loc[selected_indices].head(limit).copy()


def prepare_lottery_results(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = sort_by_date(df).copy()
    if "DrawDate" in out.columns:
        out["DrawDate"] = pd.to_datetime(out["DrawDate"], errors="coerce")
        out["_draw_day"] = out["DrawDate"].dt.date
    else:
        out["_draw_day"] = pd.NaT

    out["_game_group"] = out.apply(_lottery_group, axis=1)

    subset = [
        col
        for col in ["_draw_day", "_game_group", "GameName", "DrawType", "N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]
        if col in out.columns
    ]
    if subset:
        out = out.drop_duplicates(subset=subset, keep="first")

    return out.sort_values("DrawDate", ascending=False, na_position="last") if "DrawDate" in out.columns else out


def diverse_lottery_results(df: pd.DataFrame, limit: int = 6) -> pd.DataFrame:
    """Show a mixed latest-results sample instead of six Daily Lotto rows."""
    if df is None or df.empty:
        return pd.DataFrame()

    work = df.copy()
    if "_game_group" not in work.columns:
        work["_game_group"] = work.apply(_lottery_group, axis=1)

    selected_indices: list[int] = []

    for game in LOTTERY_DISPLAY_ORDER:
        group = work[work["_game_group"] == game]
        if not group.empty:
            selected_indices.append(group.index[0])
        if len(selected_indices) >= limit:
            break

    for idx in work.index:
        if idx not in selected_indices:
            selected_indices.append(idx)
        if len(selected_indices) >= limit:
            break

    return work.loc[selected_indices].head(limit).copy()


@st.cache_data(ttl=300, show_spinner=False)
def load_home():
    lottery_predictions = clean_lottery_predictions(cached_table("lottery_predictions", limit=600))
    lottery_results = prepare_lottery_results(cached_table("lottery_history", limit=None))
    football_picks = sort_by_strength(current_football_only(cached_table("football_fixture_predictions", limit=500)))
    football_value = sort_by_strength(current_football_only(cached_table("football_value_bets", limit=500)))
    return lottery_predictions, lottery_results, football_picks, football_value


lottery_predictions, lottery_results, football_picks, football_value = load_home()

featured_lottery = diverse_lottery_predictions(lottery_predictions, limit=6)
featured_results = diverse_lottery_results(lottery_results, limit=6)

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
    section_label("Featured Lottery Picks", "Balanced sample across the main lottery games from the latest prediction run.")
    if featured_lottery.empty:
        empty_message("No lottery picks yet", "The next refresh will populate this area.")
    else:
        cards_grid(
            [lottery_ticket_markup(row, i) for i, (_, row) in enumerate(featured_lottery.iterrows(), 1)],
            columns=3,
        )

if view in ["All", "Football"]:
    section_label("Football Value Bets", "Current/future fixtures only. Historical football rows are never shown as live picks.")
    source = football_value if not football_value.empty else football_picks
    if source.empty:
        empty_message("No football picks yet", "Football cards will return when upcoming fixtures are available.")
    else:
        cards_grid(
            [football_pick_markup(row, i) for i, (_, row) in enumerate(source.head(6).iterrows(), 1)],
            columns=3,
        )

section_label("Latest Lottery Results", "Balanced recent results across Daily Lotto, Lotto, PowerBall, and UK49s.")
if featured_results.empty:
    empty_message("No results found", "Lottery results are not available yet.")
else:
    cards_grid(
        [result_row_markup(row) for _, row in featured_results.iterrows()],
        columns=2,
    )

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
