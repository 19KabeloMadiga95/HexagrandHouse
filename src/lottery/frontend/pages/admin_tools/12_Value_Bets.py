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


st.set_page_config(
    page_title="Value Bets",
    page_icon="💰",
    layout="wide",
)

last_refresh_card()


BASE_DIR = Path(__file__).resolve().parents[4]

VALUE_BETS_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "value"
    / "football_value_bets.xlsx"
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


def filter_value_bets(df, selected_rating, selected_league, selected_market):
    filtered = df.copy()

    if selected_rating != "All" and "ValueRating" in filtered.columns:
        filtered = filtered[
            filtered["ValueRating"] == selected_rating
        ]

    if selected_league != "All" and "League" in filtered.columns:
        filtered = filtered[
            filtered["League"] == selected_league
        ]

    if selected_market != "All" and "Market" in filtered.columns:
        filtered = filtered[
            filtered["Market"] == selected_market
        ]

    return filtered


value_bets_df = safe_read_excel(
    VALUE_BETS_FILE,
    "Value_Bets"
)

all_edges_df = safe_read_excel(
    VALUE_BETS_FILE,
    "All_Market_Edges"
)

summary_df = safe_read_excel(
    VALUE_BETS_FILE,
    "Summary"
)

rating_summary_df = safe_read_excel(
    VALUE_BETS_FILE,
    "Rating_Summary"
)

league_summary_df = safe_read_excel(
    VALUE_BETS_FILE,
    "League_Summary"
)


hero_banner(
    "Value Bets",
    (
        "Compare model probability against bookmaker implied probability to find "
        "markets where the model sees a pricing edge."
    ),
    "💰"
)

st.divider()


if value_bets_df.empty and all_edges_df.empty:
    st.warning(
        "No value betting data found. Run the value bet engine first."
    )

    st.code(
        "python -m src.football.value.value_bet_engine",
        language="powershell"
    )

    st.stop()


base_df = value_bets_df.copy()

if base_df.empty:
    base_df = all_edges_df.copy()


if "FixtureDate" in base_df.columns:
    base_df["FixtureDate"] = pd.to_datetime(
        base_df["FixtureDate"],
        errors="coerce"
    )


filter_col1, filter_col2, filter_col3 = st.columns(3)

ratings = ["All"]

if "ValueRating" in base_df.columns:
    preferred_order = [
        "Strong Value",
        "Medium Value",
        "Small Value",
        "Fair Price",
        "No Value",
        "Trap Bet",
        "No Odds",
    ]

    existing_ratings = (
        base_df["ValueRating"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    ratings += [
        rating for rating in preferred_order
        if rating in existing_ratings
    ]

with filter_col1:
    selected_rating = st.selectbox(
        "Value Rating",
        ratings
    )


leagues = ["All"]

if "League" in base_df.columns:
    leagues += sorted(
        base_df["League"]
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


markets = ["All"]

if "Market" in base_df.columns:
    markets += sorted(
        base_df["Market"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

with filter_col3:
    selected_market = st.selectbox(
        "Market",
        markets
    )


filtered_df = filter_value_bets(
    base_df,
    selected_rating,
    selected_league,
    selected_market
)


if not filtered_df.empty and "ValueScore" in filtered_df.columns:
    filtered_df = filtered_df.sort_values(
        by=[
            "ValueScore",
            "ValueEdge",
            "ModelProbability",
        ],
        ascending=[
            False,
            False,
            False,
        ]
    )


strong_count = 0
medium_count = 0
avg_edge = "-"
avg_score = "-"

if not filtered_df.empty:
    if "ValueRating" in filtered_df.columns:
        strong_count = int(
            (
                filtered_df["ValueRating"] == "Strong Value"
            ).sum()
        )

        medium_count = int(
            (
                filtered_df["ValueRating"] == "Medium Value"
            ).sum()
        )

    if "ValueEdgePercent" in filtered_df.columns:
        avg_edge = round(
            pd.to_numeric(
                filtered_df["ValueEdgePercent"],
                errors="coerce"
            ).mean(),
            2
        )

    if "ValueScore" in filtered_df.columns:
        avg_score = round(
            pd.to_numeric(
                filtered_df["ValueScore"],
                errors="coerce"
            ).mean(),
            2
        )


k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    kpi_card(
        "Value Bets",
        len(filtered_df),
        "Current filter",
        "💰"
    )

with k2:
    kpi_card(
        "Strong Value",
        strong_count,
        "Best edges",
        "🔥"
    )

with k3:
    kpi_card(
        "Medium Value",
        medium_count,
        "Good edges",
        "📈"
    )

with k4:
    kpi_card(
        "Avg Edge %",
        avg_edge,
        "Model minus market",
        "⚖️"
    )

with k5:
    kpi_card(
        "Avg Value Score",
        avg_score,
        "Composite ranking",
        "🏆"
    )


st.divider()


tab1, tab2, tab3, tab4 = st.tabs(
    [
        "💰 Value Bets",
        "📊 Market Edges",
        "📈 Charts",
        "📋 Summary",
    ]
)


with tab1:

    st.subheader("💰 Ranked Value Bets")

    if filtered_df.empty:
        st.warning(
            "No value bets match your current filters."
        )

        section_card(
            "No Value Found",
            (
                "This means the current filters do not produce a positive pricing edge. "
                "That is useful information — no edge means no forced play."
            ),
            "🛡️"
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
                "Market",
                "ModelProbability",
                "BookmakerOdds",
                "BookmakerImpliedProbability",
                "ValueEdgePercent",
                "ValueRating",
                "ValueScore",
                "BettingGrade",
                "EnsembleConfidenceScore",
                "SignalCount",
                "PredictionPack",
            ]
            if col in filtered_df.columns
        ]

        st.dataframe(
            filtered_df[display_cols],
            width="stretch",
            height=720
        )


with tab2:

    st.subheader("📊 All Market Edges")

    if all_edges_df.empty:
        st.warning(
            "No all-market edge data available."
        )

    else:
        edge_df = filter_value_bets(
            all_edges_df,
            selected_rating,
            selected_league,
            selected_market
        )

        if "ValueScore" in edge_df.columns:
            edge_df = edge_df.sort_values(
                by="ValueScore",
                ascending=False
            )

        edge_cols = [
            col for col in [
                "FixtureDate",
                "League",
                "HomeTeam",
                "AwayTeam",
                "Market",
                "ModelProbability",
                "BookmakerOdds",
                "BookmakerImpliedProbability",
                "ValueEdgePercent",
                "ValueRating",
                "ValueScore",
            ]
            if col in edge_df.columns
        ]

        st.dataframe(
            edge_df[edge_cols],
            width="stretch",
            height=720
        )


with tab3:

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("🔥 Value Ratings")

        if not rating_summary_df.empty:
            plot_bar_chart(
                df=rating_summary_df,
                x_col="ValueRating",
                y_col="Markets",
                title="Markets by Value Rating",
                height=430
            )

    with chart_col2:
        st.subheader("🌍 Value Bets by League")

        if not league_summary_df.empty:
            league_chart = league_summary_df.copy()

            if "ValueBets" in league_chart.columns:
                league_chart = league_chart.sort_values(
                    by="ValueBets",
                    ascending=False
                ).head(15)

                plot_bar_chart(
                    df=league_chart,
                    x_col="League",
                    y_col="ValueBets",
                    title="Value Bets by League",
                    height=430
                )

    st.divider()

    st.subheader("📈 Best Value Scores")

    if not filtered_df.empty and "ValueScore" in filtered_df.columns:
        top_scores = filtered_df.head(20).copy()

        top_scores["Match"] = (
            top_scores["HomeTeam"].astype(str)
            + " vs "
            + top_scores["AwayTeam"].astype(str)
            + " - "
            + top_scores["Market"].astype(str)
        )

        plot_bar_chart(
            df=top_scores,
            x_col="Match",
            y_col="ValueScore",
            title="Top Value Scores",
            height=520
        )


with tab4:

    st.subheader("📋 Value Engine Summary")

    col1, col2 = st.columns(2)

    with col1:
        if summary_df.empty:
            st.warning("No summary sheet found.")
        else:
            st.dataframe(
                summary_df,
                width="stretch",
                height=360
            )

    with col2:
        if rating_summary_df.empty:
            st.warning("No rating summary found.")
        else:
            st.dataframe(
                rating_summary_df,
                width="stretch",
                height=360
            )

    st.divider()

    st.subheader("🌍 League Summary")

    if league_summary_df.empty:
        st.warning("No league summary found.")
    else:
        st.dataframe(
            league_summary_df,
            width="stretch",
            height=420
        )


st.divider()

section_card(
    "Value Bet Logic",
    (
        "Value is calculated as model probability minus bookmaker implied probability. "
        "A positive edge means the model estimates a higher chance than the market price implies."
    ),
    "💡"
)