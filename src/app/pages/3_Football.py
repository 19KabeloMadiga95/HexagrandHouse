from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.utils.sqlite_runtime import (
    cached_table, sort_by_strength, unique_options, filter_value,
    count_rows,
)
from src.app.components.website import (
    hero, mini_cards, section_label, football_pick, football_pick_markup,
    cards_grid, empty_message, friendly_table, page_footer,
)

configure_page("Football Picks", "⚽")
refresh_chip()


def current_football_only(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    date_col = None

    for col in ["FixtureDate", "MatchDate", "Date"]:
        if col in out.columns:
            date_col = col
            break

    if date_col is None:
        return pd.DataFrame()

    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
    today = pd.Timestamp.today().normalize()

    return out[out[date_col].notna() & (out[date_col] >= today)].copy()

@st.cache_data(ttl=300, show_spinner=False)
def load_football():
    # Website football must be current/future only.
    # Historical football_predictions and football_top_plays stay available in
    # admin/reporting, but they should not drive public match cards.
    fixture_predictions = sort_by_strength(
        current_football_only(cached_table("football_fixture_predictions", limit=500))
    )
    value = sort_by_strength(
        current_football_only(cached_table("football_value_bets", limit=1000))
    )
    top = fixture_predictions
    predictions = fixture_predictions
    return top, value, predictions

top, value, predictions = load_football()
league_source = top if not top.empty else predictions
leagues = unique_options(league_source, "League")
selected_league = st.selectbox("League", leagues, index=0)

view_top = filter_value(top, "League", selected_league)
view_value = filter_value(value, "League", selected_league)
view_predictions = filter_value(predictions, "League", selected_league)

hero(
    "Football Picks",
    "Review top football matches, probabilities, and value bets curated from current fixture data only.",
    eyebrow="Football intelligence",
    chips=["Current fixtures", "Value bets", "No stale cards", "Simple review"],
    metrics=[
        {"value": f"{len(view_top):,}", "label": "Top picks"},
        {"value": f"{len(view_value):,}", "label": "Value picks"},
        {"value": f"{max(len(leagues)-1, 0):,}", "label": "Leagues"},
        {"value": f"{count_rows('football_fixtures'):,}", "label": "Upcoming"},
    ],
)

mini_cards([
    {"icon": "⚽", "label": "Current view", "value": selected_league, "note": "selected league"},
    {"icon": "🔥", "label": "Top picks", "value": f"{len(view_top):,}", "note": "shortlist"},
    {"icon": "💎", "label": "Value picks", "value": f"{len(view_value):,}", "note": "extra review"},
    {"icon": "📋", "label": "Upcoming", "value": f"{count_rows('football_fixtures'):,}", "note": "fixtures"},
])

left, right = st.columns([1.05, .95], gap="large")

with left:
    section_label("Match Cards", "Review the strongest available football picks.")
    card_df = view_top if not view_top.empty else view_predictions
    if card_df.empty:
        empty_message("No match picks yet", "Football picks will populate when upcoming fixture data is available.")
    else:
        cards_grid(
            [football_pick_markup(row, i) for i, (_, row) in enumerate(card_df.head(8).iterrows(), 1)],
            columns=2,
        )

with right:
    section_label("Value Picks", "A second view for matches that may be worth comparing.")
    if view_value.empty:
        empty_message("No value picks", "This area will populate when value data is available.")
    else:
        for i, (_, row) in enumerate(view_value.head(6).iterrows(), 1):
            football_pick(row, i)

with st.expander("Show simple football table", expanded=False):
    friendly_table(
        view_predictions if not view_predictions.empty else view_top,
        ["MatchDate", "League", "HomeTeam", "AwayTeam", "PrimaryMarketSignal", "ConfidenceScore", "ConfidenceLabel"],
        height=420,
        limit=120,
    )

page_footer()
