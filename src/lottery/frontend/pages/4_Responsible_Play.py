from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st

from lottery.frontend.components.kpi_cards import (
    section_card,
    kpi_card,
    last_refresh_card,
)


st.set_page_config(
    page_title="Responsible Play",
    page_icon="🛡️",
    layout="wide",
)


def load_main_css():
    css_path = (
        Path(__file__).resolve().parents[1]
        / "styles"
        / "main.css"
    )

    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )


load_main_css()
last_refresh_card()


st.markdown(
    """<div class="hgh-premium-hero-small"><div class="hgh-hero-kicker">RESPONSIBLE PLAY</div><h1 class="hgh-hero-title-small">Smart Decisions First</h1><p class="hgh-hero-subtitle-small">HexagrandHouse is designed for analytical entertainment, not guaranteed outcomes. Every prediction carries uncertainty.</p></div>""",
    unsafe_allow_html=True
)

st.divider()


st.markdown("## 🛡️ Core Principles")

c1, c2, c3 = st.columns(3)

with c1:
    kpi_card(
        "No Guarantees",
        "Always",
        "Predictions are probabilistic",
        "📊"
    )

with c2:
    kpi_card(
        "Entertainment First",
        "Priority",
        "Never rely on betting for income",
        "🎯"
    )

with c3:
    kpi_card(
        "Selective Decision Making",
        "Recommended",
        "Avoid emotional chasing",
        "🧠"
    )


st.divider()


left_col, right_col = st.columns([1.3, 1])

with left_col:
    section_card(
        "Understanding Probability",
        (
            "A strong prediction is not a guaranteed outcome. "
            "Even high-confidence selections can lose because sports and lotteries "
            "contain randomness and external factors."
        ),
        "📈"
    )

    section_card(
        "Avoid Chasing Losses",
        (
            "Do not increase spending after losses in an attempt to recover quickly. "
            "This usually leads to emotional decision-making and unnecessary risk."
        ),
        "🚫"
    )

    section_card(
        "Use Bankroll Limits",
        (
            "Set clear spending limits before engaging with any form of betting or gaming. "
            "Never spend money required for essential living expenses."
        ),
        "💰"
    )

    section_card(
        "Take Breaks",
        (
            "Healthy decision-making requires emotional balance. "
            "If betting becomes stressful or obsessive, step away and reset."
        ),
        "🧘"
    )

with right_col:
    st.markdown(
        """<div class="hgh-responsible-panel"><div class="hgh-responsible-title">Healthy Usage Guidelines</div><ul class="hgh-responsible-list"><li>Only play with disposable income</li><li>Never force bets</li><li>Ignore hype and emotion</li><li>Focus on long-term discipline</li><li>Take regular breaks</li><li>Avoid impulsive decisions</li><li>Understand that losses happen</li></ul></div>""",
        unsafe_allow_html=True
    )


st.divider()


section_card(
    "Platform Philosophy",
    (
        "HexagrandHouse aims to provide structured analytical insights, "
        "clean data presentation and intelligent probability signals. "
        "The platform should support disciplined thinking, not emotional gambling."
    ),
    "🏆"
)