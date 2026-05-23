from pathlib import Path

import pandas as pd
import streamlit as st

from src.lottery.frontend.components.kpi_cards import (
    kpi_card,
    section_card,
    hero_banner,
    last_refresh_card,
)


st.set_page_config(
    page_title="Lottery Reports",
    page_icon="📋",
    layout="wide",
)

last_refresh_card()


BASE_DIR = Path(__file__).resolve().parents[4]

REPORTING_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "reporting"
)

QUALITY_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "quality"
    / "lottery_quality_report.xlsx"
)

EXECUTIVE_REPORT = (
    REPORTING_DIR
    / "executive_lottery_report.xlsx"
)

DAILY_SUMMARY = (
    REPORTING_DIR
    / "daily_lottery_summary.xlsx"
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


def display_dataframe(df, height=450):
    if df.empty:
        st.warning("No data found.")
    else:
        st.dataframe(
            df,
            width="stretch",
            height=height
        )


def dataframe_to_csv(df):
    return df.to_csv(
        index=False
    ).encode("utf-8")


hero_banner(
    "Lottery Reports",
    "Executive reports, daily summaries and quality-control outputs.",
    "📋"
)

st.divider()


summary_df = clean_dataframe(
    safe_read_excel(
        EXECUTIVE_REPORT,
        "Executive_Summary"
    )
)

daily_snapshot_df = clean_dataframe(
    safe_read_excel(
        DAILY_SUMMARY,
        "Today_Snapshot"
    )
)

quality_summary_df = clean_dataframe(
    safe_read_excel(
        QUALITY_FILE,
        "Summary"
    )
)


k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card(
        "Executive Report",
        "Ready" if not summary_df.empty else "Missing",
        "High-level reporting",
        "📌"
    )

with k2:
    kpi_card(
        "Daily Summary",
        "Ready" if not daily_snapshot_df.empty else "Missing",
        "Operational snapshot",
        "☀️"
    )

with k3:
    kpi_card(
        "Quality Checks",
        "Ready" if not quality_summary_df.empty else "Missing",
        "Data governance",
        "✅"
    )

with k4:
    kpi_card(
        "Report Layer",
        "Live",
        "Frontend connected",
        "📋"
    )


st.divider()

executive_tab, daily_tab, quality_tab, insights_tab = st.tabs(
    [
        "📌 Executive",
        "☀️ Daily",
        "✅ Quality",
        "📈 Insights",
    ]
)


# =========================================================
# EXECUTIVE TAB
# =========================================================

with executive_tab:

    left_col, right_col = st.columns([1.3, 1])

    with left_col:
        st.subheader("📌 Executive Summary")

        display_dataframe(
            summary_df,
            height=360
        )

        if not summary_df.empty:
            st.download_button(
                label="Download Executive Summary",
                data=dataframe_to_csv(summary_df),
                file_name="executive_summary.csv",
                mime="text/csv"
            )

    with right_col:
        section_card(
            "Executive Reporting",
            (
                "This report provides a high-level view of historical coverage, "
                "model status, quality checks and platform outputs."
            ),
            "📌"
        )

        section_card(
            "Best Use",
            (
                "Use this section when you want a management-friendly view "
                "of the platform status and latest outputs."
            ),
            "🏛️"
        )

    st.divider()

    st.subheader("Latest Results")

    latest_df = clean_dataframe(
        safe_read_excel(
            EXECUTIVE_REPORT,
            "Latest_Results"
        )
    )

    display_dataframe(
        latest_df,
        height=420
    )

    st.divider()

    st.subheader("Unified Leaderboard")

    leaderboard_df = clean_dataframe(
        safe_read_excel(
            EXECUTIVE_REPORT,
            "Unified_Leaderboard"
        )
    )

    display_dataframe(
        leaderboard_df,
        height=420
    )


# =========================================================
# DAILY TAB
# =========================================================

with daily_tab:

    snapshot_col, insights_col = st.columns([1, 1])

    with snapshot_col:
        st.subheader("☀️ Today Snapshot")

        snapshot_df = clean_dataframe(
            safe_read_excel(
                DAILY_SUMMARY,
                "Today_Snapshot"
            )
        )

        display_dataframe(
            snapshot_df,
            height=340
        )

    with insights_col:
        st.subheader("💡 Quick Insights")

        quick_insights_df = clean_dataframe(
            safe_read_excel(
                DAILY_SUMMARY,
                "Quick_Insights"
            )
        )

        display_dataframe(
            quick_insights_df,
            height=340
        )

    st.divider()

    st.subheader("Top Predictions")

    predictions_df = clean_dataframe(
        safe_read_excel(
            DAILY_SUMMARY,
            "Top_Predictions"
        )
    )

    display_dataframe(
        predictions_df,
        height=450
    )

    if not predictions_df.empty:
        st.download_button(
            label="Download Daily Predictions Summary",
            data=dataframe_to_csv(predictions_df),
            file_name="daily_predictions_summary.csv",
            mime="text/csv"
        )

    st.divider()

    st.subheader("Best Models")

    best_models_df = clean_dataframe(
        safe_read_excel(
            DAILY_SUMMARY,
            "Best_Models"
        )
    )

    display_dataframe(
        best_models_df,
        height=360
    )


# =========================================================
# QUALITY TAB
# =========================================================

with quality_tab:

    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        st.subheader("✅ Quality Summary")

        display_dataframe(
            quality_summary_df,
            height=340
        )

    with right_col:
        section_card(
            "Data Quality Layer",
            (
                "The quality-control layer checks duplicates, missing fields, "
                "invalid number ranges and latest draw coverage."
            ),
            "✅"
        )

        section_card(
            "Why This Matters",
            (
                "Prediction outputs are only as useful as the historical data "
                "feeding them. Quality checks protect the modelling layer."
            ),
            "🛡️"
        )

    st.divider()

    issue_type = st.selectbox(
        "Quality Sheet",
        [
            "Row_Counts",
            "Missing_Values",
            "Duplicate_RecordKeys",
            "Number_Range_Issues",
            "Duplicate_Number_Issues",
            "Latest_Dates",
        ]
    )

    quality_df = clean_dataframe(
        safe_read_excel(
            QUALITY_FILE,
            issue_type
        )
    )

    st.subheader(f"📋 {issue_type}")

    display_dataframe(
        quality_df,
        height=500
    )

    if not quality_df.empty:
        st.download_button(
            label=f"Download {issue_type}",
            data=dataframe_to_csv(quality_df),
            file_name=f"{issue_type.lower()}.csv",
            mime="text/csv"
        )


# =========================================================
# INSIGHTS TAB
# =========================================================

with insights_tab:

    left_col, right_col = st.columns([1.3, 1])

    with left_col:
        st.subheader("📈 Statistical Insights")

        statistical_insights_df = clean_dataframe(
            safe_read_excel(
                EXECUTIVE_REPORT,
                "Statistical_Insights"
            )
        )

        display_dataframe(
            statistical_insights_df,
            height=520
        )

    with right_col:
        section_card(
            "Interpretation Layer",
            (
                "Insights explain model behaviour, platform findings and "
                "statistical limitations in plain English."
            ),
            "📈"
        )

        section_card(
            "Important Note",
            (
                "Lottery systems remain fundamentally random. Insights "
                "describe historical tendencies only."
            ),
            "⚠️"
        )

        section_card(
            "Next Evolution",
            (
                "In Phase 2, this reporting page can be connected to a Control "
                "Center so reports can be refreshed directly from the app."
            ),
            "🚀"
        )


st.divider()

section_card(
    "Report Notes",
    (
        "Reports are generated from the latest available pipeline outputs. "
        "Quality checks validate duplicates, missing fields and invalid number "
        "ranges. Executive reports are useful for high-level review, while "
        "daily summaries are designed for operational monitoring."
    ),
    "📋"
)