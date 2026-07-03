from pathlib import Path

import pandas as pd
import streamlit as st

from HexagrandHouse_VSCode.src.app.components.kpi_cards import (
    kpi_card,
    section_card,
    hero_banner,
    last_refresh_card,
)

from HexagrandHouse_VSCode.src.app.components.football_prediction_card import (
    render_football_prediction_cards,
)


st.set_page_config(
    page_title="Top Plays Today",
    page_icon="🔥",
    layout="wide",
)

last_refresh_card()


BASE_DIR = Path(__file__).resolve().parents[4]

FIXTURE_PREDICTIONS_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "predictions"
    / "football_fixture_predictions.xlsx"
)


@st.cache_data
def safe_read_excel(path, sheet_name=0):
    try:
        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )
    except Exception:
        return pd.DataFrame()


def filter_top_plays(df, selected_grade, selected_league):
    filtered = df.copy()

    if "ElitePrediction" in filtered.columns:
        filtered = filtered[
            filtered["ElitePrediction"] == 1
        ]

    if "BettingGrade" in filtered.columns:
        filtered = filtered[
            filtered["BettingGrade"].isin(
                [
                    "S Tier",
                    "A Tier",
                    "B Tier",
                ]
            )
        ]

    if selected_grade != "All" and "BettingGrade" in filtered.columns:
        filtered = filtered[
            filtered["BettingGrade"] == selected_grade
        ]

    if selected_league != "All" and "League" in filtered.columns:
        filtered = filtered[
            filtered["League"] == selected_league
        ]

    return filtered


fixtures_df = safe_read_excel(
    FIXTURE_PREDICTIONS_FILE,
    "Fixture_Predictions"
)


hero_banner(
    "Top Plays Today",
    (
        "Curated football picks filtered to the strongest daily prediction signals. "
        "This page focuses on elite-grade opportunities only."
    ),
    "🔥"
)

st.divider()


if fixtures_df.empty:
    st.warning(
        "No fixture prediction data found. Run the fixture prediction pipeline first."
    )

    st.code(
        "python -m src.football.predictions.predict_fixtures",
        language="powershell"
    )

    st.stop()


fixtures_df["FixtureDate"] = pd.to_datetime(
    fixtures_df["FixtureDate"],
    errors="coerce"
)


filter_col1, filter_col2 = st.columns(2)

grades = ["All"]

if "BettingGrade" in fixtures_df.columns:
    grades += [
        grade for grade in [
            "S Tier",
            "A Tier",
            "B Tier",
            "C Tier",
            "Avoid",
        ]
        if grade in fixtures_df["BettingGrade"].dropna().astype(str).unique()
    ]

with filter_col1:
    selected_grade = st.selectbox(
        "Betting Grade",
        grades
    )


leagues = ["All"]

if "League" in fixtures_df.columns:
    leagues += sorted(
        fixtures_df["League"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

with filter_col2:
    selected_league = st.selectbox(
        "League",
        leagues
    )


top_plays_df = filter_top_plays(
    fixtures_df,
    selected_grade,
    selected_league
)


if not top_plays_df.empty and "EnsembleConfidenceScore" in top_plays_df.columns:
    top_plays_df = top_plays_df.sort_values(
        by=[
            "BettingGrade",
            "EnsembleConfidenceScore",
            "SignalCount",
        ],
        ascending=[
            True,
            False,
            False,
        ]
    )


k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card(
        "Top Plays",
        len(top_plays_df),
        "Filtered elite picks",
        "🔥"
    )

with k2:
    kpi_card(
        "Leagues",
        (
            top_plays_df["League"].nunique()
            if "League" in top_plays_df.columns
            else 0
        ),
        "Included leagues",
        "🌍"
    )

with k3:
    avg_conf = "-"

    if (
        not top_plays_df.empty
        and "EnsembleConfidenceScore" in top_plays_df.columns
    ):
        avg_conf = round(
            pd.to_numeric(
                top_plays_df["EnsembleConfidenceScore"],
                errors="coerce"
            ).mean(),
            3
        )

    kpi_card(
        "Avg Confidence",
        avg_conf,
        "Top plays only",
        "📈"
    )

with k4:
    best_grade = "-"

    if not top_plays_df.empty and "BettingGrade" in top_plays_df.columns:
        best_grade = str(
            top_plays_df["BettingGrade"]
            .dropna()
            .astype(str)
            .min()
        )

    kpi_card(
        "Best Grade",
        best_grade,
        "Highest available tier",
        "🏆"
    )


st.divider()


tab1, tab2 = st.tabs(
    [
        "🔥 Cards",
        "📋 Table",
    ]
)


with tab1:

    if top_plays_df.empty:
        st.warning(
            "No top plays found for the current filters."
        )

        section_card(
            "No Top Plays",
            (
                "This means no fixtures currently meet the elite signal and "
                "grade filters. That is fine — no bet is better than a weak bet."
            ),
            "🛡️"
        )

    else:
        render_football_prediction_cards(
            top_plays_df,
            max_cards=20
        )


with tab2:

    st.subheader("📋 Top Plays Table")

    if top_plays_df.empty:
        st.warning(
            "No top plays available."
        )

    else:
        display_cols = [
            col for col in [
                "FixtureDate",
                "KickoffTime",
                "Tier",
                "Country",
                "League",
                "HomeTeam",
                "AwayTeam",
                "PredictedResult",
                "PredictedResultProbability",
                "BestGoalsPick",
                "BestGoalsProbability",
                "BestCornersPick",
                "BestCornersProbability",
                "SignalCount",
                "ElitePrediction",
                "BettingGrade",
                "EnsembleConfidenceScore",
                "EnsembleConfidenceLabel",
                "PredictionPack",
            ]
            if col in top_plays_df.columns
        ]

        st.dataframe(
            top_plays_df[display_cols],
            width="stretch",
            height=720
        )


st.divider()

section_card(
    "Top Plays Logic",
    (
        "Top Plays are selected from fixtures marked as elite predictions and "
        "graded as S Tier, A Tier or B Tier. This page is intentionally selective."
    ),
    "🎯"
)