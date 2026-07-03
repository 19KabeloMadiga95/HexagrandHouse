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


st.set_page_config(
    page_title="League Analytics",
    page_icon="🌍",
    layout="wide",
)

last_refresh_card()


BASE_DIR = Path(__file__).resolve().parents[4]

PERFORMANCE_DASHBOARD = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "reporting"
    / "football_model_performance_dashboard.xlsx"
)

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


def filter_df(df, tier, country, league):
    filtered = df.copy()

    if tier != "All" and "Tier" in filtered.columns:
        filtered = filtered[filtered["Tier"] == tier]

    if country != "All" and "Country" in filtered.columns:
        filtered = filtered[filtered["Country"] == country]

    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"] == league]

    return filtered


league_performance_df = safe_read_excel(
    PERFORMANCE_DASHBOARD,
    "League_Performance"
)

fixture_predictions_df = safe_read_excel(
    FIXTURE_PREDICTIONS_FILE,
    "Fixture_Predictions"
)


hero_banner(
    "League Analytics",
    (
        "Compare football leagues by prediction coverage, confidence levels, "
        "elite pick counts and model signal strength."
    ),
    "🌍"
)

st.divider()


if fixture_predictions_df.empty:
    st.warning(
        "No fixture prediction data found. Run the football pipeline first."
    )

    st.code(
        "python -m src.football.predictions.predict_fixtures\n"
        "python -m src.football.reporting.football_model_performance_dashboard",
        language="powershell"
    )

    st.stop()


filter_col1, filter_col2, filter_col3 = st.columns(3)

tiers = ["All"]

if "Tier" in fixture_predictions_df.columns:
    tiers += sorted(
        fixture_predictions_df["Tier"]
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


country_base = fixture_predictions_df.copy()

if selected_tier != "All" and "Tier" in country_base.columns:
    country_base = country_base[
        country_base["Tier"] == selected_tier
    ]

countries = ["All"]

if "Country" in country_base.columns:
    countries += sorted(
        country_base["Country"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

with filter_col2:
    selected_country = st.selectbox(
        "Country",
        countries
    )


league_base = country_base.copy()

if selected_country != "All" and "Country" in league_base.columns:
    league_base = league_base[
        league_base["Country"] == selected_country
    ]

leagues = ["All"]

if "League" in league_base.columns:
    leagues += sorted(
        league_base["League"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

with filter_col3:
    selected_league = st.selectbox(
        "League",
        leagues
    )


filtered_fixtures = filter_df(
    fixture_predictions_df,
    selected_tier,
    selected_country,
    selected_league
)

filtered_performance = filter_df(
    league_performance_df,
    selected_tier,
    selected_country,
    selected_league
)


total_fixtures = len(filtered_fixtures)

league_count = (
    filtered_fixtures["League"].nunique()
    if "League" in filtered_fixtures.columns
    else 0
)

elite_count = (
    int(filtered_fixtures["ElitePrediction"].sum())
    if "ElitePrediction" in filtered_fixtures.columns
    else 0
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


k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card(
        "Fixtures",
        total_fixtures,
        "Filtered rows",
        "📅"
    )

with k2:
    kpi_card(
        "Leagues",
        league_count,
        "Filtered competitions",
        "🌍"
    )

with k3:
    kpi_card(
        "Elite Picks",
        elite_count,
        "High-confidence rows",
        "🔥"
    )

with k4:
    kpi_card(
        "Avg Confidence",
        avg_confidence,
        "Ensemble score",
        "📈"
    )


st.divider()


tab1, tab2, tab3 = st.tabs(
    [
        "📊 League Rankings",
        "📈 Charts",
        "📋 Model Performance",
    ]
)


with tab1:

    st.subheader("📊 League Prediction Rankings")

    if filtered_fixtures.empty:
        st.warning(
            "No league rows available for this filter."
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
                RowsWithCorners=("HasCornersPrediction", "sum"),
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

        league_summary["EliteRate"] = (
            league_summary["ElitePredictions"]
            / league_summary["Fixtures"]
        ).round(3)

        league_summary = league_summary.sort_values(
            by=[
                "AvgConfidence",
                "ElitePredictions",
            ],
            ascending=[
                False,
                False,
            ]
        )

        st.dataframe(
            league_summary,
            width="stretch",
            height=680
        )


with tab2:

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:

        st.subheader("📈 Average Confidence by League")

        if not filtered_fixtures.empty:
            chart_df = (
                filtered_fixtures
                .groupby("League", dropna=False)
                .agg(
                    AvgConfidence=("EnsembleConfidenceScore", "mean")
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
                title="Top Leagues by Avg Confidence",
                height=430
            )

    with chart_col2:

        st.subheader("🔥 Elite Picks by League")

        if not filtered_fixtures.empty:
            elite_chart = (
                filtered_fixtures
                .groupby("League", dropna=False)
                .agg(
                    ElitePredictions=("ElitePrediction", "sum")
                )
                .reset_index()
                .sort_values(
                    by="ElitePredictions",
                    ascending=False
                )
                .head(15)
            )

            plot_bar_chart(
                df=elite_chart,
                x_col="League",
                y_col="ElitePredictions",
                title="Elite Predictions by League",
                height=430
            )


with tab3:

    st.subheader("📋 League Model Performance Extract")

    if filtered_performance.empty:
        st.warning(
            "No performance dashboard data available for this filter."
        )

        section_card(
            "Run Reporting",
            (
                "Run the football model performance dashboard script to refresh "
                "league-level model analytics."
            ),
            "📋"
        )

        st.code(
            "python -m src.football.reporting.football_model_performance_dashboard",
            language="powershell"
        )

    else:
        display_cols = [
            col for col in filtered_performance.columns
        ]

        st.dataframe(
            filtered_performance[display_cols],
            width="stretch",
            height=700
        )


st.divider()

section_card(
    "League Analytics Purpose",
    (
        "This page helps compare where the football models are strongest by league, "
        "confidence level and signal count. It is useful for deciding which leagues "
        "deserve more focus in future model tuning."
    ),
    "🌍"
)