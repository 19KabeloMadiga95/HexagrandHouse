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
    page_title="Admin Center",
    page_icon="⚙️",
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
    """<div class="hgh-premium-hero-small"><div class="hgh-hero-kicker">ADMIN CENTER</div><h1 class="hgh-hero-title-small">Platform Operations</h1><p class="hgh-hero-subtitle-small">Internal platform management, diagnostics, reporting, monitoring and development tools.</p></div>""",
    unsafe_allow_html=True
)

st.divider()


st.markdown("## ⚙ Platform Status")

k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card(
        "Football Engine",
        "Online",
        "Prediction pipeline active",
        "⚽"
    )

with k2:
    kpi_card(
        "Lottery Engine",
        "Online",
        "Prediction systems active",
        "🎲"
    )

with k3:
    kpi_card(
        "Automation",
        "Healthy",
        "Daily cycle operational",
        "🔄"
    )

with k4:
    kpi_card(
        "Frontend",
        "Active",
        "Premium interface loaded",
        "🖥️"
    )


st.divider()


st.markdown("## 🧰 Admin Modules")

a1, a2 = st.columns(2)

with a1:
    section_card(
        "Control Center",
        (
            "Operational monitoring page for tracking exports, "
            "logs, diagnostics and automation status."
        ),
        "🛠️"
    )

    section_card(
        "Model Performance",
        (
            "Model summary reporting, historical outputs "
            "and lightweight dashboard exports."
        ),
        "📈"
    )

with a2:
    section_card(
        "Reports",
        (
            "Top plays, reporting outputs and supporting export files."
        ),
        "📄"
    )

    section_card(
        "Developer Utilities",
        (
            "Raw diagnostics, testing pages and experimental features."
        ),
        "🧪"
    )


st.divider()


st.markdown("## 🗂 Internal Page Structure")

st.markdown(
    """
```text
admin_tools/
│
├── 6_Control_Center.py
├── 7_Football_Home.py
├── 8_Fixture_Predictions.py
├── 9_League_Analytics.py
├── 10_Model_Performance.py
├── 11_Top_Plays.py
└── 12_Value_Bets.py
"""
)

section_card(
"Platform Direction",
(
"HexagrandHouse is transitioning from a developer-focused analytics "
"workspace into a premium user-focused sports and lottery intelligence platform."
),
"🚀"
)

st.divider()

st.markdown(
"""<div class="hgh-footer-note">Administrative tools remain available internally while the frontend experience evolves into a streamlined premium platform.</div>""",
unsafe_allow_html=True
)