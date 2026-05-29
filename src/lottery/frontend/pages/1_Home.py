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

from database.query_service import (
    get_platform_summary,
    get_latest_lottery_history,
    get_recent_football_results,
    get_top_football_predictions,
    get_model_accuracy_summary,
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


@st.cache_data(ttl=300)
def load_platform_data():
    lottery_df = get_latest_lottery_history(500)

    football_df = get_recent_football_results(
        days=14,
        limit=500
    )

    top_predictions_df = get_top_football_predictions(50)

    accuracy_df = get_model_accuracy_summary()

    db_summary_df = get_platform_summary()

    return {
        "lottery": lottery_df,
        "football": football_df,
        "top_predictions": top_predictions_df,
        "accuracy": accuracy_df,
        "db_summary": db_summary_df,
    }


platform_data = load_platform_data()

lottery_df = platform_data["lottery"]
football_df = platform_data["football"]
top_predictions_df = platform_data["top_predictions"]
accuracy_df = platform_data["accuracy"]
db_summary_df = platform_data["db_summary"]


def get_platform_health():
    if db_summary_df.empty:
        return "Offline"

    total_rows = (
        pd.to_numeric(
            db_summary_df["RowCount"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    if total_rows <= 0:
        return "Warning"

    return "Healthy"


def get_total_platform_rows():
    if db_summary_df.empty:
        return 0

    return int(
        pd.to_numeric(
            db_summary_df["RowCount"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )


def get_latest_lottery_result(df):
    if df.empty:
        return "-"

    latest = df.iloc[0]

    game = latest.get(
        "GameName",
        latest.get(
            "GameFamily",
            "Lottery"
        )
    )

    date_value = pd.to_datetime(
        latest.get("DrawDate"),
        errors="coerce"
    )

    if pd.isna(date_value):
        return str(game)

    return f"{game} — {date_value.strftime('%Y-%m-%d')}"


def get_top_play(df):
    if df.empty:
        return "-"

    top = df.iloc[0]

    home = top.get("HomeTeam", "-")
    away = top.get("AwayTeam", "-")

    prediction = top.get(
        "PredictedResult",
        top.get(
            "ModelPick",
            "Prediction"
        )
    )

    confidence = top.get(
        "EnsembleConfidenceScore",
        top.get(
            "ConfidenceScore",
            "-"
        )
    )

    if confidence != "-":
        try:
            confidence = round(float(confidence), 2)
        except Exception:
            pass

    return f"{home} vs {away} — {prediction} ({confidence})"


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

    market = top.get(
        "Market",
        top.get(
            "PredictedResult",
            "Top Signal"
        )
    )

    rating = top.get(
        "ValueRating",
        top.get(
            "EnsembleConfidenceLabel",
            "Rated"
        )
    )

    return f"{home} vs {away} — {market} ({rating})"


def get_accuracy_value():
    if accuracy_df.empty:
        return "-"

    value = accuracy_df.iloc[0].get(
        "ResultAccuracyPct",
        None
    )

    if value is None or pd.isna(value):
        return "-"

    return f"{round(float(value), 1)}%"


latest_lottery_result = get_latest_lottery_result(
    lottery_df
)

top_play = get_top_play(
    top_predictions_df
)

top_value_bet = get_top_value_bet(
    top_predictions_df
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


button_col1, button_col2, button_col3 = st.columns([1, 1, 6])

with button_col1:
    if st.button(
        "⚽ Football",
        use_container_width=True
    ):
        st.switch_page("pages/3_Football.py")

with button_col2:
    if st.button(
        "🎲 Lottery",
        use_container_width=True
    ):
        st.switch_page("pages/2_Lottery.py")


st.divider()


st.markdown("## 🧠 Platform Control Center")

d1, d2, d3, d4 = st.columns(4)

with d1:
    kpi_card(
        "Platform Status",
        get_platform_health(),
        "Database & pipelines",
        "🟢"
    )

with d2:
    kpi_card(
        "Database Rows",
        f"{get_total_platform_rows():,}",
        "Central warehouse records",
        "🗄️"
    )

with d3:
    kpi_card(
        "Football Results",
        f"{len(football_df):,}",
        "Recent completed matches",
        "⚽"
    )

with d4:
    kpi_card(
        "Model Accuracy",
        get_accuracy_value(),
        "Historical football scoring",
        "🎯"
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
        "Best Value Signal",
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
        st.switch_page("pages/3_Football.py")

with module_col2:
    st.markdown(
        """<div class="hgh-product-card"><div class="hgh-product-icon">🎲</div><div class="hgh-product-title">Lottery Intelligence</div><div class="hgh-product-text">Track latest results, predictions, ensemble picks and lottery model outputs (Lotto, Powerball, Daily Lotto, UK49s).</div><div class="hgh-product-tags"><span>Results</span><span>Predictions</span><span>Stats</span></div></div>""",
        unsafe_allow_html=True
    )

    if st.button(
        "Open Lottery",
        use_container_width=True
    ):
        st.switch_page("pages/2_Lottery.py")


st.divider()


st.markdown("## 🗄️ Database Tables")

if db_summary_df.empty:
    st.warning("Database summary unavailable.")
else:
    st.dataframe(
        db_summary_df,
        use_container_width=True,
        height=300
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
        "well-designed decision pages backed by a central SQLite warehouse."
    ),
    "🚀"
)