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

from lottery.frontend.components.football_prediction_card import (
    render_football_prediction_cards,
)

from lottery.frontend.components.charts import (
    plot_bar_chart,
)

from database.database_connection import (
    database_exists,
    read_football_predictions,
    read_football_ensemble_predictions,
    read_football_fixtures,
)


st.set_page_config(
    page_title="Football Intelligence",
    page_icon="⚽",
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

FIXTURE_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "predictions"
    / "football_fixture_predictions.xlsx"
)

TOP_PLAYS_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "reporting"
    / "top_plays_report.xlsx"
)

VALUE_BETS_FILE = (
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


@st.cache_data(ttl=300)
def load_fixture_predictions():
    if database_exists():
        df = read_football_predictions()

        if not df.empty:
            return df

    df = safe_read_excel(
        FIXTURE_FILE,
        "Fixture_Predictions"
    )

    if df.empty:
        df = safe_read_excel(FIXTURE_FILE)

    return df


@st.cache_data(ttl=300)
def load_ensemble_predictions():
    if database_exists():
        df = read_football_ensemble_predictions()

        if not df.empty:
            return df

    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_fixtures():
    if database_exists():
        df = read_football_fixtures()

        if not df.empty:
            return df

    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_top_plays():
    df = safe_read_excel(
        TOP_PLAYS_FILE,
        "Top_Plays"
    )

    if df.empty:
        df = safe_read_excel(TOP_PLAYS_FILE)

    return df


@st.cache_data(ttl=300)
def load_value_bets():
    df = safe_read_excel(
        VALUE_BETS_FILE,
        "Value_Bets"
    )

    if df.empty:
        df = safe_read_excel(VALUE_BETS_FILE)

    return df


def prepare_fixture_df(df):
    if df.empty:
        return df

    temp = df.copy()

    numeric_cols = [
        "EnsembleConfidenceScore",
        "SignalCount",
        "ElitePrediction",
        "ValueScore",
        "ModelProbability",
        "PredictedResultProbability",
    ]

    for col in numeric_cols:
        if col in temp.columns:
            temp[col] = pd.to_numeric(
                temp[col],
                errors="coerce"
            )

    return temp


def normalise_confidence_scores(df):
    if df.empty:
        return df

    temp = df.copy()

    possible_cols = [
        "EnsembleConfidenceScore",
        "ConfidenceScore",
        "EnsembleScore",
        "RawScore",
    ]

    confidence_col = None

    for col in possible_cols:
        if col in temp.columns:
            confidence_col = col
            break

    if confidence_col is None:
        temp["EnsembleConfidenceScore"] = 0
        temp["EnsembleConfidenceLabel"] = "Unrated"
        return temp

    scores = pd.to_numeric(
        temp[confidence_col],
        errors="coerce"
    )

    if confidence_col in ["RawScore", "EnsembleScore"]:
        min_score = scores.min()
        max_score = scores.max()

        if (
            pd.notna(min_score)
            and pd.notna(max_score)
            and max_score > min_score
        ):
            scores = (
                (scores - min_score)
                / (max_score - min_score)
            ) * 100

    temp["EnsembleConfidenceScore"] = (
        scores.fillna(0)
        .round(2)
    )

    def confidence_label(score):
        try:
            score = float(score)
        except Exception:
            return "Unrated"

        if score >= 85:
            return "Elite"

        if score >= 75:
            return "High"

        if score >= 60:
            return "Medium"

        if score > 0:
            return "Low"

        return "Unrated"

    temp["EnsembleConfidenceLabel"] = (
        temp["EnsembleConfidenceScore"]
        .apply(confidence_label)
    )

    return temp


fixture_df = load_fixture_predictions()
ensemble_df = load_ensemble_predictions()
fixtures_master_df = load_fixtures()

top_plays_df = load_top_plays()
value_bets_df = load_value_bets()

fixture_df = prepare_fixture_df(fixture_df)
top_plays_df = prepare_fixture_df(top_plays_df)
value_bets_df = prepare_fixture_df(value_bets_df)

fixture_df = normalise_confidence_scores(fixture_df)
top_plays_df = normalise_confidence_scores(top_plays_df)
value_bets_df = normalise_confidence_scores(value_bets_df)


st.markdown(
    """<div class="hgh-premium-hero-small"><div class="hgh-hero-kicker">FOOTBALL INTELLIGENCE</div><h1 class="hgh-hero-title-small">Elite Football Insights</h1><p class="hgh-hero-subtitle-small">Curated football predictions, top plays and value opportunities powered by historical form, ensemble scoring and market analysis.</p></div>""",
    unsafe_allow_html=True
)

st.divider()


fixture_count = len(fixture_df)

elite_count = 0

if (
    not fixture_df.empty
    and "ElitePrediction" in fixture_df.columns
):
    elite_count = int(
        fixture_df["ElitePrediction"]
        .fillna(0)
        .astype(int)
        .sum()
    )

league_count = 0

if (
    not fixture_df.empty
    and "League" in fixture_df.columns
):
    league_count = fixture_df["League"].nunique()

avg_confidence = "-"

if (
    not fixture_df.empty
    and "EnsembleConfidenceScore" in fixture_df.columns
):
    avg_confidence = round(
        fixture_df["EnsembleConfidenceScore"].mean(),
        2
    )


k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card(
        "Fixtures",
        fixture_count,
        "Upcoming predictions",
        "⚽"
    )

with k2:
    kpi_card(
        "Elite Picks",
        elite_count,
        "High-confidence fixtures",
        "🔥"
    )

with k3:
    kpi_card(
        "Leagues",
        league_count,
        "Tracked competitions",
        "🌍"
    )

with k4:
    kpi_card(
        "Avg Confidence",
        avg_confidence,
        "Ensemble score",
        "📈"
    )


st.divider()


filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    league_options = ["All"]

    if (
        not fixture_df.empty
        and "League" in fixture_df.columns
    ):
        league_options.extend(
            sorted(
                fixture_df["League"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

    selected_league = st.selectbox(
        "League",
        options=league_options
    )

with filter_col2:
    confidence_filter = st.selectbox(
        "Confidence Filter",
        options=[
            "All",
            "Elite Only",
        ]
    )


filtered_df = fixture_df.copy()

if (
    selected_league != "All"
    and "League" in filtered_df.columns
):
    filtered_df = filtered_df[
        filtered_df["League"].astype(str)
        == selected_league
    ]

if (
    confidence_filter == "Elite Only"
    and "ElitePrediction" in filtered_df.columns
):
    filtered_df = filtered_df[
        filtered_df["ElitePrediction"]
        .fillna(0)
        .astype(int) == 1
    ]


tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🔥 Top Plays",
        "💰 Value Bets",
        "📅 Fixtures",
        "📊 Leagues",
    ]
)


with tab1:
    st.markdown("## 🔥 Elite Football Picks")

    card_df = top_plays_df.copy()

    if card_df.empty:
        card_df = filtered_df.copy()

    if (
        selected_league != "All"
        and "League" in card_df.columns
    ):
        card_df = card_df[
            card_df["League"].astype(str)
            == selected_league
        ]

    if card_df.empty:
        st.warning(
            "No football predictions available."
        )
    else:
        render_football_prediction_cards(
            card_df,
            max_cards=12
        )


with tab2:
    st.markdown("## 💰 Market Value Opportunities")

    value_display_df = value_bets_df.copy()

    if (
        selected_league != "All"
        and "League" in value_display_df.columns
    ):
        value_display_df = value_display_df[
            value_display_df["League"].astype(str)
            == selected_league
        ]

    if value_display_df.empty:
        st.warning(
            "No value bet data available."
        )

    else:
        display_cols = [
            col for col in [
                "League",
                "HomeTeam",
                "AwayTeam",
                "Market",
                "ModelProbability",
                "BookmakerOdds",
                "ValueEdgePercent",
                "ValueRating",
                "ValueScore",
                "EnsembleConfidenceScore",
                "EnsembleConfidenceLabel",
            ]
            if col in value_display_df.columns
        ]

        st.dataframe(
            value_display_df[display_cols].head(30),
            use_container_width=True,
            height=620
        )

    section_card(
        "What Is A Value Bet?",
        (
            "Value bets occur when the platform probability "
            "is higher than the implied bookmaker probability."
        ),
        "💡"
    )


with tab3:
    st.markdown("## 📅 Upcoming Fixtures")

    if filtered_df.empty:
        st.warning("No fixtures available.")

    else:
        display_cols = [
            col for col in [
                "FixtureDate",
                "KickoffTime",
                "League",
                "HomeTeam",
                "AwayTeam",
                "PredictedResult",
                "PredictedResultProbability",
                "BestGoalsPick",
                "BestCornersPick",
                "BettingGrade",
                "EnsembleConfidenceScore",
                "EnsembleConfidenceLabel",
            ]
            if col in filtered_df.columns
        ]

        st.dataframe(
            filtered_df[display_cols],
            use_container_width=True,
            height=700
        )


with tab4:
    st.markdown("## 📊 League Confidence")

    if (
        not filtered_df.empty
        and "League" in filtered_df.columns
        and "EnsembleConfidenceScore" in filtered_df.columns
    ):
        chart_df = (
            filtered_df
            .groupby("League")["EnsembleConfidenceScore"]
            .mean()
            .reset_index()
        )

        chart_df = chart_df.sort_values(
            by="EnsembleConfidenceScore",
            ascending=False
        )

        plot_bar_chart(
            chart_df,
            x_col="League",
            y_col="EnsembleConfidenceScore",
            title="Average Confidence by League"
        )

        st.dataframe(
            chart_df,
            use_container_width=True,
            height=500
        )

    else:
        st.warning(
            "No league analytics available."
        )


st.divider()

st.markdown(
    """<div class="hgh-footer-note">Football predictions and value ratings are analytical indicators only and should be used responsibly.</div>""",
    unsafe_allow_html=True
)