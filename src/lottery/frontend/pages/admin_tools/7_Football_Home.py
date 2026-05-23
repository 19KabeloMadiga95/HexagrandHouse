from pathlib import Path

import pandas as pd
import streamlit as st

from src.lottery.frontend.components.kpi_cards import (
    kpi_card,
    section_card,
    hero_banner,
    last_refresh_card,
)

from src.lottery.frontend.components.charts import (
    plot_bar_chart,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Football Analytics",
    page_icon="⚽",
    layout="wide",
)

last_refresh_card()


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[4]

FOOTBALL_MASTER_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "master"
    / "football_master_all_leagues.xlsx"
)

FIXTURE_PREDICTIONS_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "predictions"
    / "football_fixture_predictions.xlsx"
)

ENSEMBLE_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "predictions"
    / "football_ensemble_predictions.xlsx"
)

PERFORMANCE_DASHBOARD = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "reporting"
    / "football_model_performance_dashboard.xlsx"
)


# =========================================================
# HELPERS
# =========================================================

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


def safe_metric(df, col, default=0):
    if df.empty or col not in df.columns:
        return default

    return df[col].nunique()


def safe_len(df):
    if df.empty:
        return 0

    return len(df)


def format_date(value):
    try:
        return pd.to_datetime(value).strftime("%Y-%m-%d")
    except Exception:
        return "-"


def filter_dataframe(df, selected_tier, selected_league):
    filtered_df = df.copy()

    if selected_tier != "All" and "Tier" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["Tier"] == selected_tier
        ]

    if selected_league != "All" and "League" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["League"] == selected_league
        ]

    return filtered_df


# =========================================================
# LOAD DATA
# =========================================================

master_df = safe_read_excel(
    FOOTBALL_MASTER_FILE,
    "Football_Master"
)

fixture_predictions_df = safe_read_excel(
    FIXTURE_PREDICTIONS_FILE,
    "Fixture_Predictions"
)

fixture_elite_df = safe_read_excel(
    FIXTURE_PREDICTIONS_FILE,
    "Elite_Predictions"
)

ensemble_df = safe_read_excel(
    ENSEMBLE_FILE,
    "Ensemble_Predictions"
)

performance_kpis_df = safe_read_excel(
    PERFORMANCE_DASHBOARD,
    "High_Level_KPIs"
)

league_performance_df = safe_read_excel(
    PERFORMANCE_DASHBOARD,
    "League_Performance"
)


# =========================================================
# HEADER
# =========================================================

hero_banner(
    "Football Analytics Command Center",
    (
        "Unified football intelligence covering historical performance, "
        "future fixture predictions, result probabilities, goals markets, "
        "corners markets and ensemble confidence."
    ),
    "⚽"
)

st.divider()


# =========================================================
# GLOBAL FILTERS
# =========================================================

filter_col1, filter_col2 = st.columns(2)

tiers = ["All"]

if not fixture_predictions_df.empty and "Tier" in fixture_predictions_df.columns:
    tiers += sorted(
        fixture_predictions_df["Tier"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

with filter_col1:
    selected_tier = st.selectbox(
        "Filter by Tier",
        tiers
    )

leagues = ["All"]

if not fixture_predictions_df.empty and "League" in fixture_predictions_df.columns:
    temp_df = fixture_predictions_df.copy()

    if selected_tier != "All" and "Tier" in temp_df.columns:
        temp_df = temp_df[
            temp_df["Tier"] == selected_tier
        ]

    leagues += sorted(
        temp_df["League"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

with filter_col2:
    selected_league = st.selectbox(
        "Filter by League",
        leagues
    )


filtered_fixtures = filter_dataframe(
    fixture_predictions_df,
    selected_tier,
    selected_league
)

filtered_elite = filter_dataframe(
    fixture_elite_df,
    selected_tier,
    selected_league
)

filtered_ensemble = filter_dataframe(
    ensemble_df,
    selected_tier,
    selected_league
)


# =========================================================
# KPI CARDS
# =========================================================

historical_rows = safe_len(
    master_df
)

leagues_count = safe_metric(
    master_df,
    "League"
)

future_fixtures = safe_len(
    filtered_fixtures
)

elite_predictions = safe_len(
    filtered_elite
)

avg_confidence = "-"

if (
    not filtered_fixtures.empty
    and "EnsembleConfidenceScore" in filtered_fixtures.columns
):
    avg_confidence = round(
        pd.to_numeric(
            filtered_fixtures["EnsembleConfidenceScore"],
            errors="coerce"
        ).mean(),
        3
    )

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    kpi_card(
        "Historical Matches",
        historical_rows,
        "Master warehouse rows",
        "🏟️"
    )

with k2:
    kpi_card(
        "Leagues",
        leagues_count,
        "Covered competitions",
        "🌍"
    )

with k3:
    kpi_card(
        "Future Fixtures",
        future_fixtures,
        "Filtered fixture predictions",
        "📅"
    )

with k4:
    kpi_card(
        "Elite Picks",
        elite_predictions,
        "High-confidence fixtures",
        "🔥"
    )

with k5:
    kpi_card(
        "Avg Confidence",
        avg_confidence,
        "Fixture ensemble score",
        "📈"
    )


st.divider()


# =========================================================
# TABS
# =========================================================

overview_tab, elite_tab, fixtures_tab, league_tab, status_tab = st.tabs(
    [
        "📊 Overview",
        "🔥 Elite Picks",
        "📅 Fixture Predictions",
        "🌍 League View",
        "🧪 Data Status",
    ]
)


# =========================================================
# OVERVIEW TAB
# =========================================================

with overview_tab:

    left_col, right_col = st.columns([1.3, 1])

    with left_col:

        st.subheader("📈 Confidence by League")

        if (
            not filtered_fixtures.empty
            and "League" in filtered_fixtures.columns
            and "EnsembleConfidenceScore" in filtered_fixtures.columns
        ):
            chart_df = (
                filtered_fixtures
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
                title="Average Fixture Confidence",
                height=420
            )

        else:
            st.warning(
                "No fixture prediction data available for this selection."
            )

    with right_col:

        st.subheader("⚽ Platform Summary")

        section_card(
            "Football Engine",
            (
                "The football module combines historical form, goals, corners, "
                "result probabilities and future fixture data into one prediction layer."
            ),
            "⚽"
        )

        section_card(
            "Current Markets",
            (
                "Supported prediction areas: Match Result, Over Goals, BTTS "
                "and Over Corners where corner data is available."
            ),
            "🎯"
        )

        section_card(
            "Data Tiers",
            (
                "Tier 1 and Tier 2 contain richer match statistics. Tier 3 expands "
                "global coverage, mostly focused on results and goals."
            ),
            "🌍"
        )

    st.divider()

    st.subheader("🏆 Top Upcoming Predictions")

    if not filtered_fixtures.empty:
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
                "BestGoalsProbability",
                "BestCornersPick",
                "BestCornersProbability",
                "EnsembleConfidenceScore",
                "EnsembleConfidenceLabel",
                "PredictionPack",
            ]
            if col in filtered_fixtures.columns
        ]

        top_df = filtered_fixtures.copy()

        if "EnsembleConfidenceScore" in top_df.columns:
            top_df = top_df.sort_values(
                by="EnsembleConfidenceScore",
                ascending=False
            )

        st.dataframe(
            top_df[display_cols].head(20),
            width="stretch",
            height=520
        )

    else:
        st.warning("No fixture predictions found.")


# =========================================================
# ELITE PICKS TAB
# =========================================================

with elite_tab:

    st.subheader("🔥 Elite Fixture Predictions")

    if filtered_elite.empty:
        st.warning(
            "No elite fixture predictions found for the current filter."
        )

        section_card(
            "Elite Pick Logic",
            (
                "A fixture is marked elite when the ensemble confidence is strong "
                "and multiple model signals agree."
            ),
            "🔥"
        )

    else:
        elite_display_cols = [
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
                "EnsembleConfidenceScore",
                "EnsembleConfidenceLabel",
                "PredictionPack",
            ]
            if col in filtered_elite.columns
        ]

        st.dataframe(
            filtered_elite[elite_display_cols],
            width="stretch",
            height=620
        )


# =========================================================
# FIXTURE PREDICTIONS TAB
# =========================================================

with fixtures_tab:

    st.subheader("📅 All Fixture Predictions")

    if filtered_fixtures.empty:
        st.warning(
            "No fixture prediction data available."
        )

    else:
        fixtures_display_cols = [
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
                "PredictionPack",
            ]
            if col in filtered_fixtures.columns
        ]

        st.dataframe(
            filtered_fixtures[fixtures_display_cols],
            width="stretch",
            height=700
        )


# =========================================================
# LEAGUE VIEW TAB
# =========================================================

with league_tab:

    st.subheader("🌍 League Analytics")

    if filtered_fixtures.empty:
        st.warning(
            "No league data available for current filter."
        )

    else:
        league_summary = (
            filtered_fixtures
            .groupby(
                [
                    "Tier",
                    "Country",
                    "League",
                ],
                dropna=False
            )
            .agg(
                Fixtures=("League", "count"),
                ElitePredictions=("ElitePrediction", "sum"),
                AvgConfidence=("EnsembleConfidenceScore", "mean"),
                AvgResultProbability=("PredictedResultProbability", "mean"),
                AvgGoalsProbability=("BestGoalsProbability", "mean"),
                AvgCornersProbability=("BestCornersProbability", "mean"),
                AvgSignalCount=("SignalCount", "mean"),
            )
            .reset_index()
        )

        numeric_cols = [
            "AvgConfidence",
            "AvgResultProbability",
            "AvgGoalsProbability",
            "AvgCornersProbability",
            "AvgSignalCount",
        ]

        for col in numeric_cols:
            league_summary[col] = league_summary[col].round(3)

        st.dataframe(
            league_summary.sort_values(
                by="AvgConfidence",
                ascending=False
            ),
            width="stretch",
            height=620
        )

        st.divider()

        chart_df = league_summary.sort_values(
            by="Fixtures",
            ascending=False
        ).head(15)

        plot_bar_chart(
            df=chart_df,
            x_col="League",
            y_col="Fixtures",
            title="Upcoming Fixtures by League",
            height=420
        )


# =========================================================
# DATA STATUS TAB
# =========================================================

with status_tab:

    st.subheader("🧪 Football Data Status")

    status_rows = []

    files_to_check = [
        {
            "Name": "Football Master",
            "Path": FOOTBALL_MASTER_FILE,
        },
        {
            "Name": "Fixture Predictions",
            "Path": FIXTURE_PREDICTIONS_FILE,
        },
        {
            "Name": "Historical Ensemble",
            "Path": ENSEMBLE_FILE,
        },
        {
            "Name": "Performance Dashboard",
            "Path": PERFORMANCE_DASHBOARD,
        },
    ]

    for item in files_to_check:
        path = item["Path"]

        exists = path.exists()

        status_rows.append(
            {
                "File": item["Name"],
                "Exists": exists,
                "Path": str(path),
                "LastModified": (
                    pd.to_datetime(
                        path.stat().st_mtime,
                        unit="s"
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    if exists
                    else "-"
                ),
                "SizeMB": (
                    round(
                        path.stat().st_size / (1024 * 1024),
                        2
                    )
                    if exists
                    else 0
                ),
            }
        )

    status_df = pd.DataFrame(
        status_rows
    )

    st.dataframe(
        status_df,
        width="stretch",
        height=300
    )

    st.divider()

    st.subheader("📋 Performance KPI Extract")

    if performance_kpis_df.empty:
        st.warning(
            "Performance dashboard KPIs not available yet."
        )

    else:
        st.dataframe(
            performance_kpis_df,
            width="stretch",
            height=420
        )


st.divider()

section_card(
    "Football Module Direction",
    (
        "The current football module now supports historical data ingestion, "
        "feature engineering, model outputs, future fixtures and frontend visibility. "
        "Next step: dedicated fixture, league and model performance pages."
    ),
    "🚀"
)