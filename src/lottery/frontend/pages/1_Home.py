from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd
import streamlit as st

from lottery.frontend.components.kpi_cards import (
    kpi_card,
    section_card,
    last_refresh_card,
)

LOGO_PATH = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "hexagrandhouse_logo.png"
)

st.set_page_config(
    page_title="HexagrandHouse",
    page_icon="🏆",
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


BASE_DIR = Path(__file__).resolve().parents[4]

LOTTERY_RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "master"
    / "lottery_historical_master.xlsx"
)

FOOTBALL_TOP_PLAYS_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "reporting"
    / "top_plays_report.xlsx"
)

FOOTBALL_VALUE_BETS_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "value"
    / "football_value_bets.xlsx"
)


@st.cache_data(ttl=300)
def safe_read_excel(path, sheet_name=0):
    try:
        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )
    except Exception:
        return pd.DataFrame()


def get_latest_lottery_result(df):
    if df.empty:
        return "-"

    if "DrawDate" not in df.columns:
        return "-"

    temp = df.copy()

    temp["DrawDate"] = pd.to_datetime(
        temp["DrawDate"],
        errors="coerce"
    )

    temp = temp.dropna(
        subset=["DrawDate"]
    )

    if temp.empty:
        return "-"

    latest = temp.sort_values(
        by="DrawDate",
        ascending=False
    ).iloc[0]

    game = latest.get(
        "GameName",
        latest.get(
            "GameFamily",
            "Lottery"
        )
    )

    date_value = latest["DrawDate"].strftime(
        "%Y-%m-%d"
    )

    return f"{game} — {date_value}"


def get_top_play(df):
    if df.empty:
        return "-"

    required_cols = [
        "HomeTeam",
        "AwayTeam",
    ]

    for col in required_cols:
        if col not in df.columns:
            return "-"

    temp = df.copy()

    if "EnsembleConfidenceScore" in temp.columns:
        temp["EnsembleConfidenceScore"] = pd.to_numeric(
            temp["EnsembleConfidenceScore"],
            errors="coerce"
        )

        temp = temp.sort_values(
            by="EnsembleConfidenceScore",
            ascending=False
        )

    top = temp.iloc[0]

    home = top.get("HomeTeam", "-")
    away = top.get("AwayTeam", "-")
    pick = top.get("PredictedResult", "Top Play")

    return f"{home} vs {away} — {pick}"


def get_top_value_bet(df):
    if df.empty:
        return "-"

    temp = df.copy()

    if "ValueScore" in temp.columns:
        temp["ValueScore"] = pd.to_numeric(
            temp["ValueScore"],
            errors="coerce"
        )

        temp = temp.sort_values(
            by="ValueScore",
            ascending=False
        )

    top = temp.iloc[0]

    home = top.get("HomeTeam", "-")
    away = top.get("AwayTeam", "-")
    market = top.get("Market", "Value Market")
    rating = top.get("ValueRating", "Value")

    return f"{home} vs {away} — {market} ({rating})"


lottery_df = safe_read_excel(
    LOTTERY_RESULTS_FILE
)

top_plays_df = safe_read_excel(
    FOOTBALL_TOP_PLAYS_FILE,
    "Top_Plays"
)

value_bets_df = safe_read_excel(
    FOOTBALL_VALUE_BETS_FILE,
    "Value_Bets"
)


latest_lottery_result = get_latest_lottery_result(
    lottery_df
)

top_play = get_top_play(
    top_plays_df
)

top_value_bet = get_top_value_bet(
    value_bets_df
)

logo_col1, logo_col2 = st.columns([1, 7])

with logo_col1:
    st.image(
        str(LOGO_PATH),
        width=130
    )

with logo_col2:
    st.markdown(
        """<div style="padding-top:38px;"><div style="font-size:13px;letter-spacing:4px;color:#f5b700;font-weight:800;">PREMIUM ANALYTICS PLATFORM</div><div style="font-size:15px;color:#9aa4b2;padding-top:6px;">Advanced Football & Lottery Intelligence Engine</div></div>""",
        unsafe_allow_html=True
    )
st.markdown(
    """<div class="hgh-premium-hero"><div class="hgh-hero-left"><div class="hgh-hero-kicker">HEXAGRANDHOUSE</div><h1 class="hgh-hero-title">Data. Insight. <span>Play Smart.</span></h1><p class="hgh-hero-subtitle">A premium analytics platform for lottery intelligence, football predictions, value opportunities and responsible decision-making.</p></div><div class="hgh-hero-right"><div class="hgh-glow-card"><div class="hgh-glow-card-title">Today’s Signal</div><div class="hgh-glow-card-main">Premium Picks</div><div class="hgh-glow-card-sub">Curated outputs from active models, confidence scoring and market-value checks.</div></div></div></div>""",
    unsafe_allow_html=True
)


button_col1, button_col2, button_col3 = st.columns(
    [
        1,
        1,
        6,
    ]
)

with button_col1:
    if st.button(
        "⚽ Football",
        use_container_width=True
    ):
        st.switch_page(
            "pages/3_Football.py"
        )

with button_col2:
    if st.button(
        "🎲 Lottery",
        use_container_width=True
    ):
        st.switch_page(
            "pages/2_Lottery.py"
        )


st.divider()


st.markdown("## 🔥 Today's Highlights")

h1, h2, h3 = st.columns(3)

with h1:
    section_card(
        "Top Football Play",
        top_play,
        "⚽"
    )

with h2:
    section_card(
        "Best Value Bet",
        top_value_bet,
        "💰"
    )

with h3:
    section_card(
        "Latest Lottery Result",
        latest_lottery_result,
        "🎲"
    )


st.divider()


st.markdown("## 🏆 Choose Your Arena")

module_col1, module_col2 = st.columns(2)

with module_col1:
    st.markdown(
        """<div class="hgh-product-card"><div class="hgh-product-icon">⚽</div><div class="hgh-product-title">Football Intelligence</div><div class="hgh-product-text">View top plays, value bets, fixtures and league-level insights from the football engine.</div><div class="hgh-product-tags"><span>Top Plays</span><span>Value Bets</span><span>Fixtures</span></div></div>""",
        unsafe_allow_html=True
    )

    if st.button(
        "Open Football",
        use_container_width=True
    ):
        st.switch_page(
            "pages/3_Football.py"
        )

with module_col2:
    st.markdown(
        """<div class="hgh-product-card"><div class="hgh-product-icon">🎲</div><div class="hgh-product-title">Lottery Intelligence</div><div class="hgh-product-text">Track latest results, predictions, ensemble picks and lottery model outputs (Lotto, Powerball, Daily Lotto, UK49s).</div><div class="hgh-product-tags"><span>Results</span><span>Predictions</span><span>Stats</span></div></div>""",
        unsafe_allow_html=True
    )

    if st.button(
        "Open Lottery",
        use_container_width=True
    ):
        st.switch_page(
            "pages/2_Lottery.py"
        )


st.divider()


st.markdown("## 🛡️ Responsible Intelligence")

r1, r2, r3 = st.columns(3)

with r1:
    kpi_card(
        "Data Driven",
        "Yes",
        "Historical data and model signals",
        "📊"
    )

with r2:
    kpi_card(
        "Selective Picks",
        "Curated",
        "No forced plays",
        "🎯"
    )

with r3:
    kpi_card(
        "Responsible Play",
        "Always",
        "Entertainment, not certainty",
        "🛡️"
    )


st.divider()


section_card(
    "Platform Direction",
    (
        "HexagrandHouse is being shaped into a clean premium user platform. "
        "The engine stays powerful behind the scenes, while users see simple, useful, "
        "well-designed decision pages."
    ),
    "🚀"
)