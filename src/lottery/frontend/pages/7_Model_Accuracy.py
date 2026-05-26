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
    last_refresh_card,
)

from lottery.frontend.components.charts import (
    plot_bar_chart,
)


st.set_page_config(
    page_title="Football Model Accuracy",
    page_icon="📊",
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

BACKTEST_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "backtesting"
    / "football_fixture_backtest_history.xlsx"
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


def find_existing_column(df, possible_cols):
    for col in possible_cols:
        if col in df.columns:
            return col

    return None


def convert_rate_columns_to_percent(df):
    df = df.copy()

    rate_cols = [
        "ResultHitRate",
        "GoalsHitRate",
        "CornersHitRate",
        "ResultAccuracy",
        "GoalsAccuracy",
        "CornersAccuracy",
    ]

    for col in rate_cols:
        if col in df.columns:
            df[col] = (
                pd.to_numeric(
                    df[col],
                    errors="coerce"
                )
                * 100
            ).round(1)

    return df


history_df = safe_read_excel(
    BACKTEST_FILE,
    "Backtest_History"
)

summary_df = safe_read_excel(
    BACKTEST_FILE,
    "Summary"
)

league_df = safe_read_excel(
    BACKTEST_FILE,
    "League_Summary"
)

grade_df = safe_read_excel(
    BACKTEST_FILE,
    "Grade_Summary"
)


st.markdown(
    """<div class="hgh-premium-hero-small"><div class="hgh-hero-kicker">MODEL ACCURACY</div><h1 class="hgh-hero-title-small">Prediction Performance Tracking</h1><p class="hgh-hero-subtitle-small">Historical scoring engine comparing football predictions against completed real-world match outcomes.</p></div>""",
    unsafe_allow_html=True
)

st.divider()


total_backtests = len(history_df)

result_hit_rate = "-"
goals_hit_rate = "-"
corners_hit_rate = "-"

if not history_df.empty:

    if "ResultHit" in history_df.columns:
        result_hit_rate = round(
            pd.to_numeric(
                history_df["ResultHit"],
                errors="coerce"
            ).mean() * 100,
            1
        )

    if "GoalsHit" in history_df.columns:
        goals_hit_rate = round(
            pd.to_numeric(
                history_df["GoalsHit"],
                errors="coerce"
            ).mean() * 100,
            1
        )

    if "CornersHit" in history_df.columns:
        corners_hit_rate = round(
            pd.to_numeric(
                history_df["CornersHit"],
                errors="coerce"
            ).mean() * 100,
            1
        )


k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card(
        "Fixtures Scored",
        total_backtests,
        "Historical evaluations",
        "⚽"
    )

with k2:
    kpi_card(
        "Result Accuracy",
        f"{result_hit_rate}%",
        "Match outcome hit rate",
        "🎯"
    )

with k3:
    kpi_card(
        "Goals Accuracy",
        f"{goals_hit_rate}%",
        "Goals market performance",
        "🔥"
    )

with k4:
    kpi_card(
        "Corners Accuracy",
        f"{corners_hit_rate}%",
        "Corners market performance",
        "📈"
    )


st.divider()


tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Summary",
        "🌍 Leagues",
        "🏆 Betting Grades",
        "📋 Match History",
    ]
)


with tab1:

    st.markdown("## 📊 Overall Model Performance")

    if summary_df.empty:
        st.warning(
            "No backtesting summary available."
        )
    else:
        st.dataframe(
            summary_df,
            use_container_width=True,
            height=350
        )

    if (
        not history_df.empty
        and "ResultHit" in history_df.columns
    ):
        date_col = find_existing_column(
            history_df,
            [
                "ResultDate",
                "FixtureDate",
                "MatchDate",
            ]
        )

        if date_col:
            trend_df = history_df.copy()

            trend_df[date_col] = pd.to_datetime(
                trend_df[date_col],
                errors="coerce"
            )

            trend_df = trend_df.dropna(
                subset=[date_col]
            )

            trend_df = (
                trend_df
                .groupby(date_col)["ResultHit"]
                .mean()
                .reset_index()
            )

            trend_df["AccuracyPct"] = (
                pd.to_numeric(
                    trend_df["ResultHit"],
                    errors="coerce"
                )
                * 100
            ).round(1)

            plot_bar_chart(
                trend_df.tail(20),
                x_col=date_col,
                y_col="AccuracyPct",
                title="Recent Result Accuracy %",
                height=350
            )
        else:
            st.warning(
                "No valid result date column found for accuracy trend."
            )


with tab2:

    st.markdown("## 🌍 League Performance")

    if league_df.empty:
        st.warning(
            "No league summary available."
        )
    else:
        display_df = convert_rate_columns_to_percent(
            league_df
        )

        sort_col = find_existing_column(
            display_df,
            [
                "ResultHitRate",
                "ResultAccuracy",
            ]
        )

        if sort_col:
            display_df = display_df.sort_values(
                by=sort_col,
                ascending=False
            )

        st.dataframe(
            display_df,
            use_container_width=True,
            height=650
        )

        if sort_col and "League" in display_df.columns:
            plot_bar_chart(
                display_df.head(15),
                x_col="League",
                y_col=sort_col,
                title="Top League Accuracy %",
                height=420
            )


with tab3:

    st.markdown("## 🏆 Betting Grade Performance")

    if grade_df.empty:
        st.warning(
            "No betting grade summary available."
        )
    else:
        display_df = convert_rate_columns_to_percent(
            grade_df
        )

        sort_col = find_existing_column(
            display_df,
            [
                "ResultHitRate",
                "ResultAccuracy",
            ]
        )

        if sort_col:
            display_df = display_df.sort_values(
                by=sort_col,
                ascending=False
            )

        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )

        if sort_col and "BettingGrade" in display_df.columns:
            plot_bar_chart(
                display_df,
                x_col="BettingGrade",
                y_col=sort_col,
                title="Accuracy By Betting Grade",
                height=380
            )


with tab4:

    st.markdown("## 📋 Historical Prediction Results")

    if history_df.empty:
        st.warning(
            "No historical backtests available."
        )
    else:
        display_cols = [
            col for col in [
                "FixtureDate",
                "League",
                "HomeTeam",
                "AwayTeam",
                "PredictedResult",
                "ActualResult",
                "ActualHomeGoals",
                "ActualAwayGoals",
                "ResultHit",
                "BestGoalsPick",
                "GoalsHit",
                "BestCornersPick",
                "CornersHit",
                "BettingGrade",
                "EnsembleConfidenceLabel",
            ]
            if col in history_df.columns
        ]

        display_df = history_df.copy()

        for col in [
            "ResultHit",
            "GoalsHit",
            "CornersHit",
        ]:
            if col in display_df.columns:
                display_df[col] = display_df[col].map(
                    {
                        1: "✅",
                        0: "❌",
                    }
                )

        st.dataframe(
            display_df[display_cols],
            use_container_width=True,
            height=750
        )


st.divider()

st.markdown(
    """<div class="hgh-footer-note">Football prediction accuracy is continuously monitored using completed fixture results and historical market scoring.</div>""",
    unsafe_allow_html=True
)