from pathlib import Path

import pandas as pd
import streamlit as st

from HexagrandHouse_VSCode.src.app.components.kpi_cards import (
    kpi_card,
    section_card,
    hero_banner,
    last_refresh_card,
)

from HexagrandHouse_VSCode.src.app.components.charts import (
    plot_bar_chart,
)

from HexagrandHouse_VSCode.src.app.components.football_prediction_card import (
    render_football_prediction_cards,
)


st.set_page_config(
    page_title="Fixture Predictions",
    page_icon="📅",
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


def filter_df(df, tier, league, confidence, elite_only):
    filtered = df.copy()

    if tier != "All" and "Tier" in filtered.columns:
        filtered = filtered[filtered["Tier"] == tier]

    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"] == league]

    if confidence != "All" and "EnsembleConfidenceLabel" in filtered.columns:
        filtered = filtered[
            filtered["EnsembleConfidenceLabel"] == confidence
        ]

    if elite_only and "ElitePrediction" in filtered.columns:
        filtered = filtered[
            filtered["ElitePrediction"] == 1
        ]

    return filtered


fixtures_df = safe_read_excel(
    FIXTURE_PREDICTIONS_FILE,
    "Fixture_Predictions"
)

summary_df = safe_read_excel(
    FIXTURE_PREDICTIONS_FILE,
    "Summary"
)

league_summary_df = safe_read_excel(
    FIXTURE_PREDICTIONS_FILE,
    "League_Summary"
)


hero_banner(
    "Fixture Predictions",
    (
        "Upcoming football fixtures with result probabilities, goals picks, "
        "corners picks and ensemble confidence scoring."
    ),
    "📅"
)

st.divider()


if fixtures_df.empty:
    st.warning(
        "No fixture prediction data found. Run the fixture prediction pipeline first."
    )

    st.code(
        "python -m src.football.data_ingestion.build_football_fixtures\n"
        "python -m src.football.predictions.predict_fixtures",
        language="powershell"
    )

    st.stop()


fixtures_df["FixtureDate"] = pd.to_datetime(
    fixtures_df["FixtureDate"],
    errors="coerce"
)


filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

tiers = ["All"]

if "Tier" in fixtures_df.columns:
    tiers += sorted(
        fixtures_df["Tier"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

with filter_col1:
    selected_tier = st.selectbox(
        "Tier",
        tiers
    )


league_base_df = fixtures_df.copy()

if selected_tier != "All" and "Tier" in league_base_df.columns:
    league_base_df = league_base_df[
        league_base_df["Tier"] == selected_tier
    ]

leagues = ["All"]

if "League" in league_base_df.columns:
    leagues += sorted(
        league_base_df["League"]
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


confidence_options = ["All"]

if "EnsembleConfidenceLabel" in fixtures_df.columns:
    confidence_options += sorted(
        fixtures_df["EnsembleConfidenceLabel"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

with filter_col3:
    selected_confidence = st.selectbox(
        "Confidence",
        confidence_options
    )

with filter_col4:
    elite_only = st.toggle(
        "Elite only",
        value=False
    )


filtered_df = filter_df(
    fixtures_df,
    selected_tier,
    selected_league,
    selected_confidence,
    elite_only
)


k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    kpi_card(
        "Fixtures",
        len(filtered_df),
        "Current filter",
        "📅"
    )

with k2:
    kpi_card(
        "Leagues",
        (
            filtered_df["League"].nunique()
            if "League" in filtered_df.columns
            else 0
        ),
        "Competitions",
        "🌍"
    )

with k3:
    kpi_card(
        "Elite Picks",
        (
            int(filtered_df["ElitePrediction"].sum())
            if "ElitePrediction" in filtered_df.columns
            else 0
        ),
        "High-confidence",
        "🔥"
    )

with k4:
    avg_conf = "-"

    if (
        not filtered_df.empty
        and "EnsembleConfidenceScore" in filtered_df.columns
    ):
        avg_conf = round(
            pd.to_numeric(
                filtered_df["EnsembleConfidenceScore"],
                errors="coerce"
            ).mean(),
            3
        )

    kpi_card(
        "Avg Confidence",
        avg_conf,
        "Ensemble score",
        "📈"
    )

with k5:
    next_fixture = "-"

    if not filtered_df.empty and "FixtureDate" in filtered_df.columns:
        next_fixture = str(
            filtered_df["FixtureDate"]
            .dropna()
            .min()
            .date()
        )

    kpi_card(
        "Next Fixture",
        next_fixture,
        "Earliest date",
        "⏱️"
    )


st.divider()


tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📅 Predictions",
        "🔥 Elite Picks",
        "📊 Charts",
        "📋 Summary",
    ]
)


with tab1:

    st.subheader("📅 Fixture Prediction Table")

    display_cols = [
        col for col in [
            "FixtureDate",
            "KickoffTime",
            "Tier",
            "Country",
            "League",
            "HomeTeam",
            "AwayTeam",
            "HomeWinProbability",
            "DrawProbability",
            "AwayWinProbability",
            "PredictedResult",
            "PredictedResultProbability",
            "ExpectedTotalGoals",
            "BestGoalsPick",
            "BestGoalsProbability",
            "ExpectedTotalCorners",
            "BestCornersPick",
            "BestCornersProbability",
            "SignalCount",
            "ElitePrediction",
            "EnsembleConfidenceScore",
            "EnsembleConfidenceLabel",
            "BettingGrade",
            "PredictionPack",
        ]
        if col in filtered_df.columns
    ]

    if filtered_df.empty:
        st.warning(
            "No fixtures match your current filters."
        )

    else:
        table_df = filtered_df.copy()

        if "EnsembleConfidenceScore" in table_df.columns:
            table_df = table_df.sort_values(
                by=[
                    "FixtureDate",
                    "EnsembleConfidenceScore",
                ],
                ascending=[
                    True,
                    False,
                ]
            )

        st.dataframe(
            table_df[display_cols],
            width="stretch",
            height=720
        )


with tab2:

    st.subheader("🔥 Elite Fixture Picks")

    elite_filtered = filtered_df.copy()

    if "ElitePrediction" in elite_filtered.columns:
        elite_filtered = elite_filtered[
            elite_filtered["ElitePrediction"] == 1
        ]

    if elite_filtered.empty:
        st.warning(
            "No elite picks found for this filter."
        )

        section_card(
            "Elite Logic",
            (
                "Elite picks require a strong ensemble confidence score "
                "and multiple aligned model signals."
            ),
            "🔥"
        )

    else:
        st.subheader("🔥 Elite Prediction Cards")

        render_football_prediction_cards(
            elite_filtered,
            max_cards=10
        )

        st.divider()

        elite_cols = [
            col for col in [
                "FixtureDate",
                "KickoffTime",
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
                "EnsembleConfidenceScore",
                "BettingGrade",
                "PredictionPack",
            ]
            if col in elite_filtered.columns
        ]

        elite_filtered = elite_filtered.sort_values(
            by=[
                "EnsembleConfidenceScore",
                "SignalCount",
            ],
            ascending=[
                False,
                False,
            ]
        )

        st.subheader("📋 Elite Pick Table")

        st.dataframe(
            elite_filtered[elite_cols],
            width="stretch",
            height=650
        )


with tab3:

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📈 Average Confidence by League")

        if (
            not filtered_df.empty
            and "League" in filtered_df.columns
            and "EnsembleConfidenceScore" in filtered_df.columns
        ):
            chart_df = (
                filtered_df
                .groupby("League", dropna=False)
                .agg(
                    AvgConfidence=("EnsembleConfidenceScore", "mean"),
                    Fixtures=("League", "count"),
                )
                .reset_index()
                .sort_values(
                    by="AvgConfidence",
                    ascending=False
                )
                .head(15)
            )

            chart_df["AvgConfidence"] = chart_df[
                "AvgConfidence"
            ].round(3)

            plot_bar_chart(
                df=chart_df,
                x_col="League",
                y_col="AvgConfidence",
                title="Average Confidence by League",
                height=430
            )

    with right_col:
        st.subheader("📊 Fixtures by League")

        if (
            not filtered_df.empty
            and "League" in filtered_df.columns
        ):
            fixture_chart = (
                filtered_df
                .groupby("League", dropna=False)
                .size()
                .reset_index(name="Fixtures")
                .sort_values(
                    by="Fixtures",
                    ascending=False
                )
                .head(15)
            )

            plot_bar_chart(
                df=fixture_chart,
                x_col="League",
                y_col="Fixtures",
                title="Fixture Count by League",
                height=430
            )


with tab4:

    st.subheader("📋 Fixture Prediction Summary")

    col1, col2 = st.columns(2)

    with col1:
        if summary_df.empty:
            st.warning("No summary sheet found.")
        else:
            st.dataframe(
                summary_df,
                width="stretch",
                height=400
            )

    with col2:
        if league_summary_df.empty:
            st.warning("No league summary sheet found.")
        else:
            st.dataframe(
                league_summary_df,
                width="stretch",
                height=400
            )


st.divider()

section_card(
    "Daily Use",
    (
        "This page is designed for quick fixture review. Use the filters to narrow "
        "by tier, league, confidence band or elite-only selections."
    ),
    "📌"
)