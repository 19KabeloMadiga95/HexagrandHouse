from pathlib import Path

import pandas as pd
import streamlit as st

from HexagrandHouse_VSCode.src.app.components.kpi_cards import (
    kpi_card,
    status_card,
    hero_banner,
    last_refresh_card,
    section_card,
)

from HexagrandHouse_VSCode.src.app.components.charts import (
    plot_bar_chart,
)


st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide",
)

last_refresh_card()


BASE_DIR = Path(__file__).resolve().parents[4]

MASTER_FILE = (
    BASE_DIR
    / "data"
    / "master"
    / "lottery_historical_master.xlsx"
)

LEADERBOARD_FILE = (
    BASE_DIR
    / "data"
    / "exports"
    / "backtesting"
    / "unified_model_performance_dashboard.xlsx"
)

ENSEMBLE_FILE = (
    BASE_DIR
    / "data"
    / "exports"
    / "final_predictions"
    / "all_games_ensemble_predictions.xlsx"
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


def clean_dataframe(df):
    if df.empty:
        return df

    df = df.copy()

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str)

    return df


master_df = clean_dataframe(
    safe_read_excel(MASTER_FILE)
)

leaderboard_df = clean_dataframe(
    safe_read_excel(
        LEADERBOARD_FILE,
        "Unified_Leaderboard"
    )
)

ensemble_df = clean_dataframe(
    safe_read_excel(
        ENSEMBLE_FILE,
        "All_Ensemble_Predictions"
    )
)


hero_banner(
    "HexagrandHouse Command Dashboard",
    (
        "Central view of historical coverage, model performance, "
        "recent results, final ensembles and platform health."
    ),
    "📊"
)

st.divider()


historical_rows = (
    len(master_df)
    if not master_df.empty
    else 0
)

games_covered = (
    master_df["GameFamily"].nunique()
    if not master_df.empty and "GameFamily" in master_df.columns
    else 0
)

latest_draw = "-"

if not master_df.empty and "DrawDate" in master_df.columns:
    try:
        latest_draw = str(
            pd.to_datetime(
                master_df["DrawDate"],
                errors="coerce"
            ).max().date()
        )
    except Exception:
        latest_draw = "-"

top_model = "-"

if not leaderboard_df.empty and "ModelName" in leaderboard_df.columns:
    top_model = str(
        leaderboard_df.iloc[0]["ModelName"]
    )


kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    kpi_card(
        "Historical Rows",
        historical_rows,
        "Total records loaded",
        "📚"
    )

with kpi_col2:
    kpi_card(
        "Games Covered",
        games_covered,
        "Lottery families",
        "🎲"
    )

with kpi_col3:
    kpi_card(
        "Latest Draw",
        latest_draw,
        "Newest result",
        "📅"
    )

with kpi_col4:
    kpi_card(
        "Top Model",
        top_model,
        "Unified best performer",
        "🏆"
    )


st.divider()

overview_tab, leaderboard_tab, ensembles_tab, status_tab = st.tabs(
    [
        "📊 Overview",
        "🏆 Leaderboard",
        "🧠 Ensembles",
        "⚙️ Platform Status",
    ]
)


# =========================================================
# OVERVIEW TAB
# =========================================================

with overview_tab:

    overview_left, overview_right = st.columns([1.2, 1])

    with overview_left:
        st.subheader("🎯 Recent Results")

        if master_df.empty:
            st.warning("No historical data found.")

        else:
            latest_results = master_df.copy()

            if "DrawDate" in latest_results.columns:
                latest_results["DrawDate"] = pd.to_datetime(
                    latest_results["DrawDate"],
                    errors="coerce"
                )

                latest_results = latest_results.sort_values(
                    by="DrawDate",
                    ascending=False
                )

            preferred_cols = [
                "GameFamily",
                "GameName",
                "DrawType",
                "DrawDate",
                "N1",
                "N2",
                "N3",
                "N4",
                "N5",
                "N6",
                "Bonus",
            ]

            cols = [
                c for c in preferred_cols
                if c in latest_results.columns
            ]

            st.dataframe(
                latest_results[cols].head(15),
                width="stretch",
                height=450
            )

    with overview_right:
        st.subheader("📌 Platform Snapshot")

        section_card(
            "Phase 1 Engine",
            (
                "Historical ingestion, quality checks, feature engineering, "
                "base predictions, model comparison, optimization and reporting "
                "are now connected."
            ),
            "🚀"
        )

        section_card(
            "Phase 2A UX Polish",
            (
                "The dashboard is now moving from a report-style layout into "
                "a tabbed analytics application experience."
            ),
            "✨"
        )

        section_card(
            "Football Module Reminder",
            (
                "The current platform structure is game-agnostic, which means "
                "football analytics can be added as the next major module."
            ),
            "⚽"
        )


# =========================================================
# LEADERBOARD TAB
# =========================================================

with leaderboard_tab:

    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        st.subheader("🏆 Unified Model Leaderboard")

        if leaderboard_df.empty:
            st.warning("No unified leaderboard data found.")

        else:
            display_cols = [
                col for col in [
                    "UnifiedRank",
                    "GameFamily",
                    "ModelName",
                    "AverageBestRegularMatch_PerDraw",
                    "DrawsWithAtLeast3RegularMatches",
                    "BonusHitDrawRate",
                ]
                if col in leaderboard_df.columns
            ]

            st.dataframe(
                leaderboard_df[display_cols].head(15),
                width="stretch",
                height=500
            )

    with right_col:
        st.subheader("📈 Model Performance")

        if (
            not leaderboard_df.empty
            and "ModelName" in leaderboard_df.columns
            and "AverageBestRegularMatch_PerDraw" in leaderboard_df.columns
        ):
            chart_df = leaderboard_df.copy()

            chart_df["AverageBestRegularMatch_PerDraw"] = pd.to_numeric(
                chart_df["AverageBestRegularMatch_PerDraw"],
                errors="coerce"
            )

            chart_df = chart_df.dropna(
                subset=["AverageBestRegularMatch_PerDraw"]
            )

            if "GameFamily" in chart_df.columns:
                chart_df["ChartLabel"] = (
                    chart_df["GameFamily"].astype(str)
                    + " | "
                    + chart_df["ModelName"].astype(str)
                )
            else:
                chart_df["ChartLabel"] = chart_df["ModelName"].astype(str)

            if not chart_df.empty:
                chart_df = chart_df.sort_values(
                    by="AverageBestRegularMatch_PerDraw",
                    ascending=True
                ).tail(10)

                plot_bar_chart(
                    df=chart_df,
                    x_col="ChartLabel",
                    y_col="AverageBestRegularMatch_PerDraw",
                    title="Top 10 Model Performance",
                    height=420
                )

        st.divider()

        section_card(
            "Leaderboard Logic",
            (
                "The leaderboard combines model comparison results across "
                "PowerBall, Lotto, Daily Lotto and UK49s."
            ),
            "🏆"
        )


# =========================================================
# ENSEMBLES TAB
# =========================================================

with ensembles_tab:

    ensemble_left, ensemble_right = st.columns([1.4, 1])

    with ensemble_left:
        st.subheader("🧠 Final Ensemble Picks")

        if ensemble_df.empty:
            st.warning("No final ensemble predictions found.")

        else:
            st.dataframe(
                ensemble_df.head(30),
                width="stretch",
                height=500
            )

    with ensemble_right:
        st.subheader("📈 Ensemble Score View")

        if (
            not ensemble_df.empty
            and "EnsembleScore" in ensemble_df.columns
        ):
            chart_df = ensemble_df.copy()

            chart_df["EnsembleScore"] = pd.to_numeric(
                chart_df["EnsembleScore"],
                errors="coerce"
            )

            chart_df = chart_df.dropna(
                subset=["EnsembleScore"]
            )

            if "GameFamily" in chart_df.columns and "EnsembleRank" in chart_df.columns:
                chart_df["ChartLabel"] = (
                    chart_df["GameFamily"].astype(str)
                    + " Rank "
                    + chart_df["EnsembleRank"].astype(str)
                )
            else:
                chart_df["ChartLabel"] = chart_df.index.astype(str)

            chart_df = chart_df.sort_values(
                by="EnsembleScore",
                ascending=True
            ).tail(15)

            if not chart_df.empty:
                plot_bar_chart(
                    df=chart_df,
                    x_col="ChartLabel",
                    y_col="EnsembleScore",
                    title="Top Ensemble Scores",
                    height=420
                )

        st.divider()

        section_card(
            "Final Ensemble Engine",
            (
                "Final predictions combine base model outputs, genetic optimizer "
                "results, rank strength, agreement scoring and diversity controls."
            ),
            "🧠"
        )


# =========================================================
# STATUS TAB
# =========================================================

with status_tab:

    status_left, status_right = st.columns([1, 1])

    with status_left:
        st.subheader("⚙️ Platform Status")

        s1, s2 = st.columns(2)

        with s1:
            status_card(
                "Historical Ingestion",
                "Operational",
                "📥"
            )

            status_card(
                "Prediction Engine",
                "Operational",
                "🎯"
            )

            status_card(
                "Reporting Layer",
                "Operational",
                "📋"
            )

        with s2:
            status_card(
                "Feature Engineering",
                "Operational",
                "🛠️"
            )

            status_card(
                "Optimization Engine",
                "Operational",
                "🧬"
            )

            status_card(
                "Ensemble Engine",
                "Operational",
                "🧠"
            )

    with status_right:
        st.subheader("📌 Platform Insights")

        st.info(
            "Unified model comparison is active across PowerBall, Lotto, Daily Lotto and UK49s."
        )

        st.info(
            "Final ensemble predictions are generated from base model outputs and genetic optimizer results."
        )

        st.info(
            "Random baseline is intentionally tracked because it tells us whether model logic is adding value."
        )

        st.info(
            "HexagrandHouse Phase 1 is functioning as a modular lottery analytics platform."
        )