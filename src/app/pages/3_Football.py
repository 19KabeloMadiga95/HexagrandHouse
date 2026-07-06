from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.utils.sqlite_runtime import (
    cached_table, sort_by_strength, unique_options, filter_value,
    count_rows,
)
from src.app.components.website import (
    hero, mini_cards, section_label, football_pick, empty_message,
    friendly_table, page_footer,
)

configure_page("Football Picks", "⚽")
refresh_chip()

@st.cache_data(ttl=300, show_spinner=False)
def load_football():
    top = sort_by_strength(cached_table("football_top_plays", limit=500))
    value = sort_by_strength(cached_table("football_value_bets", limit=1000))
    predictions = sort_by_strength(cached_table("football_predictions", limit=5000))
    if top.empty:
        top = predictions
    return top, value, predictions

top, value, predictions = load_football()
league_source = top if not top.empty else predictions
leagues = unique_options(league_source, "League")
selected_league = st.selectbox("Choose a league", leagues, index=0)

view_top = filter_value(top, "League", selected_league)
view_value = filter_value(value, "League", selected_league)
view_predictions = filter_value(predictions, "League", selected_league)

hero(
    "Football picks.",
    "A simple match list for reviewing suggested football picks. Start with the cards, then open the table only when you need more detail.",
    eyebrow="Football",
    chips=["Top matches", "Value view", "Simple cards"],
    metrics=[
        {"value": f"{len(view_top):,}", "label": "Top picks"},
        {"value": f"{len(view_value):,}", "label": "Value picks"},
        {"value": f"{max(len(leagues)-1, 0):,}", "label": "Leagues"},
        {"value": f"{count_rows('football_history'):,}", "label": "Past matches"},
    ],
)

mini_cards([
    {"icon": "⚽", "label": "Current view", "value": selected_league, "note": "selected league"},
    {"icon": "🔥", "label": "Top picks", "value": f"{len(view_top):,}", "note": "shortlist"},
    {"icon": "💎", "label": "Value picks", "value": f"{len(view_value):,}", "note": "extra review"},
    {"icon": "📋", "label": "Past matches", "value": f"{count_rows('football_history'):,}", "note": "loaded results"},
])

left, right = st.columns([1.05, .95], gap="large")

with left:
    section_label("Match cards", "Review the strongest available football picks.")
    card_df = view_top if not view_top.empty else view_predictions
    if card_df.empty:
        empty_message("No match picks yet", "Football picks will populate when data is available.")
    else:
        for i, (_, row) in enumerate(card_df.head(8).iterrows(), 1):
            football_pick(row, i)

with right:
    section_label("Value picks", "A second view for matches that may be worth comparing.")
    if view_value.empty:
        empty_message("No value picks", "This area will populate when value data is available.")
    else:
        for i, (_, row) in enumerate(view_value.head(5).iterrows(), 1):
            football_pick(row, i)

with st.expander("Show simple football table", expanded=False):
    friendly_table(
        view_predictions if not view_predictions.empty else view_top,
        ["MatchDate", "League", "HomeTeam", "AwayTeam", "PrimaryMarketSignal", "ConfidenceScore", "ConfidenceLabel"],
        height=420,
        limit=120,
    )

page_footer()
