from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.website import hero, mini_cards, section_label, page_footer

configure_page("Settings", "⚙")
refresh_chip()

hero(
    "Settings & Responsible Play",
    "HexaGrandBet is an analytics and entertainment platform. It does not guarantee outcomes and it is not a bookmaker.",
    eyebrow="Platform policy",
    chips=["18+", "No guarantees", "Budget first", "Statistical review"],
    metrics=[
        {"value": "18+", "label": "Adults only"},
        {"value": "Limit", "label": "Set a budget"},
        {"value": "Stop", "label": "Never chase"},
        {"value": "Review", "label": "Data only"},
    ],
)

mini_cards([
    {"icon": "🧾", "label": "Rule 1", "value": "Set a hard limit", "note": "Only use money already allocated for entertainment."},
    {"icon": "🛑", "label": "Rule 2", "value": "No promises", "note": "Random systems remain random."},
    {"icon": "🧠", "label": "Rule 3", "value": "No chasing", "note": "Never increase stakes to recover losses."},
    {"icon": "🌱", "label": "Rule 4", "value": "Keep balance", "note": "Stop if play becomes stressful."},
])

section_label("Platform stance")
st.markdown(
    """
    <div class="hh-content-card">
        <p>
        HexaGrandBet makes lottery and football review easier. It should not encourage unhealthy behaviour.
        Use the platform as an information and entertainment website. Picks, trends, and confidence indicators are not guarantees.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

page_footer()
