from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.components.website import hero, mini_cards, section_label, page_footer

configure_page("Play Smart", "🛡️")
refresh_chip()

hero(
    "Play smart.",
    "HexagrandHouse is built for review and entertainment. Picks can help you compare options, but they can never promise an outcome.",
    eyebrow="Responsible play",
    chips=["No guarantees", "Budget first", "Stay in control"],
    metrics=[
        {"value": "Limit", "label": "Set a budget"},
        {"value": "Stop", "label": "Never chase"},
        {"value": "Review", "label": "Think clearly"},
        {"value": "Balance", "label": "Life first"},
    ],
)

mini_cards([
    {"icon": "🧾", "label": "Rule 1", "value": "Set a hard limit", "note": "Only use money already allocated for entertainment."},
    {"icon": "🛑", "label": "Rule 2", "value": "Predictions are not promises", "note": "Random systems remain random."},
    {"icon": "🧠", "label": "Rule 3", "value": "No chasing", "note": "Never increase stakes to recover losses."},
    {"icon": "🌱", "label": "Rule 4", "value": "Keep balance", "note": "Stop if play becomes stressful."},
])

section_label("Platform stance")
st.markdown(
    """
    <div class="hh-content-card">
        <p style="color:#dbeafe;line-height:1.7;margin:0;">
        HexagrandHouse should make review easier, not encourage unhealthy behaviour.
        Use it as a simple information website, keep play optional, and step away when it no longer feels recreational.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

page_footer()
