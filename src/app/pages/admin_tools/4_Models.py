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
    plot_line_chart,
)


st.set_page_config(
    page_title="Model Analytics",
    page_icon="🧠",
    layout="wide",
)

last_refresh_card()


BASE_DIR = Path(__file__).resolve().parents[4]

UNIFIED_DASHBOARD = (
    BASE_DIR
    / "data"
    / "exports"
    / "backtesting"
    / "unified_model_performance_dashboard.xlsx"
)

POWERBALL_GENETIC_FILE = (
    BASE_DIR
    / "data"
    / "exports"
    / "optimization"
    / "powerball_genetic_optimizer_results.xlsx"
)

LOTTO_GENETIC_FILE = (
    BASE_DIR
    / "data"
    / "exports"
    / "optimization"
    / "lotto_genetic_optimizer_results.xlsx"
)

DAILY_LOTTO_GENETIC_FILE = (
    BASE_DIR
    / "data"
    / "exports"
    / "optimization"
    / "daily_lotto_genetic_optimizer_results.xlsx"
)

UK49S_GENETIC_FILE = (
    BASE_DIR
    / "data"
    / "exports"
    / "optimization"
    / "uk49s_genetic_optimizer_results.xlsx"
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


hero_banner(
    "Lottery Model Analytics",
    (
        "Unified backtesting, optimization and adaptive tuning performance."
    ),
    "🧠"
)

st.divider()


leaderboard_df = clean_dataframe(
    safe_read_excel(
        UNIFIED_DASHBOARD,
        "Unified_Leaderboard"
    )
)

powerball_genetic_df = clean_dataframe(
    safe_read_excel(
        POWERBALL_GENETIC_FILE,
        "Top_Combinations"
    )
)

lotto_genetic_df = clean_dataframe(
    safe_read_excel(
        LOTTO_GENETIC_FILE,
        "Top_Combinations"
    )
)

daily_lotto_genetic_df = clean_dataframe(
    safe_read_excel(
        DAILY_LOTTO_GENETIC_FILE,
        "Top_Combinations"
    )
)

uk49s_genetic_df = clean_dataframe(
    safe_read_excel(
        UK49S_GENETIC_FILE,
        "Top_Combinations"
    )
)


games_compared = (
    leaderboard_df["GameFamily"].nunique()
    if not leaderboard_df.empty
    and "GameFamily" in leaderboard_df.columns
    else 0
)

models_compared = (
    leaderboard_df["ModelName"].nunique()
    if not leaderboard_df.empty
    and "ModelName" in leaderboard_df.columns
    else 0
)

top_game = "-"

if (
    not leaderboard_df.empty
    and "GameFamily" in leaderboard_df.columns
):
    top_game = str(
        leaderboard_df.iloc[0]["GameFamily"]
    )

top_model = "-"

if (
    not leaderboard_df.empty
    and "ModelName" in leaderboard_df.columns
):
    top_model = str(
        leaderboard_df.iloc[0]["ModelName"]
    )


k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card(
        "Games Compared",
        games_compared,
        "Cross-game leaderboard",
        "🎲"
    )

with k2:
    kpi_card(
        "Models Compared",
        models_compared,
        "Unified model rows",
        "🏆"
    )

with k3:
    kpi_card(
        "Top Game",
        top_game,
        "Best current performer",
        "🥇"
    )

with k4:
    kpi_card(
        "Top Model",
        top_model,
        "Best overall model",
        "🧠"
    )


st.divider()

leaderboard_tab, optimizer_tab, tuner_tab, insights_tab = st.tabs(
    [
        "🏆 Leaderboard",
        "🧬 Optimizers",
        "⚙️ Tuner",
        "📋 Insights",
    ]
)


# =========================================================
# LEADERBOARD TAB
# =========================================================

with leaderboard_tab:

    left_col, right_col = st.columns([1.3, 1])

    with left_col:

        st.subheader("🏆 Unified Model Leaderboard")

        if leaderboard_df.empty:
            st.warning("No unified leaderboard data found.")

        else:

            display_cols = [
                col for col in [
                    "UnifiedRank",
                    "GameFamily",
                    "Rank",
                    "ModelName",
                    "DrawsTested",
                    "AverageBestRegularMatch_PerDraw",
                    "DrawsWithAtLeast3RegularMatches",
                    "BonusHitDrawRate",
                ]
                if col in leaderboard_df.columns
            ]

            st.dataframe(
                leaderboard_df[display_cols],
                width="stretch",
                height=560
            )

    with right_col:

        st.subheader("📈 Cross-Game Performance")

        if (
            not leaderboard_df.empty
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

            if (
                "GameFamily" in chart_df.columns
                and "ModelName" in chart_df.columns
            ):
                chart_df["ModelLabel"] = (
                    chart_df["GameFamily"].astype(str)
                    + " | "
                    + chart_df["ModelName"].astype(str)
                )

            chart_df = chart_df.sort_values(
                by="AverageBestRegularMatch_PerDraw",
                ascending=True
            ).tail(20)

            plot_bar_chart(
                df=chart_df,
                x_col="ModelLabel",
                y_col="AverageBestRegularMatch_PerDraw",
                title="Cross-Game Model Performance",
                height=480
            )

        st.divider()

        section_card(
            "Unified Model Engine",
            (
                "This leaderboard combines model comparison outputs across "
                "PowerBall, Lotto, Daily Lotto and UK49s."
            ),
            "📊"
        )


# =========================================================
# OPTIMIZER TAB
# =========================================================

with optimizer_tab:

    optimizer_option = st.selectbox(
        "Select Optimizer Output",
        [
            "PowerBall",
            "Lotto",
            "Daily Lotto",
            "UK49s",
        ]
    )

    optimizer_map = {
        "PowerBall": powerball_genetic_df,
        "Lotto": lotto_genetic_df,
        "Daily Lotto": daily_lotto_genetic_df,
        "UK49s": uk49s_genetic_df,
    }

    optimizer_df = optimizer_map[optimizer_option]

    left_col, right_col = st.columns([1.3, 1])

    with left_col:

        st.subheader(
            f"🧬 {optimizer_option} Genetic Optimizer"
        )

        if optimizer_df.empty:
            st.warning("No optimizer output found.")

        else:
            st.dataframe(
                optimizer_df,
                width="stretch",
                height=560
            )

    with right_col:

        st.subheader("📈 Fitness Performance")

        if (
            not optimizer_df.empty
            and "FitnessScore" in optimizer_df.columns
        ):

            top_fitness = optimizer_df.copy()

            top_fitness["FitnessScore"] = pd.to_numeric(
                top_fitness["FitnessScore"],
                errors="coerce"
            )

            top_fitness = top_fitness.dropna(
                subset=["FitnessScore"]
            )

            top_fitness = top_fitness.head(15)

            top_fitness["Label"] = (
                top_fitness.index.astype(str)
            )

            plot_line_chart(
                df=top_fitness,
                x_col="Label",
                y_col="FitnessScore",
                title="Top Genetic Optimizer Fitness Scores",
                height=420
            )

        st.divider()

        section_card(
            "Optimizer Engine",
            (
                "Genetic optimizers evolve candidate combinations using "
                "fitness scoring, mutation, crossover and ranking systems."
            ),
            "🧬"
        )


# =========================================================
# TUNER TAB
# =========================================================

with tuner_tab:

    st.subheader("⚙️ Adaptive Weight Tuner")

    tuner_placeholder = pd.DataFrame(
        {
            "Parameter": [
                "Recent Weight",
                "Historical Weight",
                "Diversity Weight",
                "Pairing Weight",
                "Anti-Crowding Weight",
            ],
            "Status": [
                "Prepared",
                "Prepared",
                "Prepared",
                "Prepared",
                "Prepared",
            ],
            "Phase": [
                "Phase 2",
                "Phase 2",
                "Phase 2",
                "Phase 2",
                "Phase 2",
            ]
        }
    )

    left_col, right_col = st.columns([1, 1])

    with left_col:

        st.dataframe(
            tuner_placeholder,
            width="stretch",
            height=320
        )

    with right_col:

        section_card(
            "Adaptive Tuning",
            (
                "The adaptive tuning layer is designed to automatically "
                "adjust model weights based on recent performance."
            ),
            "⚙️"
        )

        section_card(
            "Current Status",
            (
                "The tuner architecture is ready, but active automated "
                "re-weighting is currently disabled during Phase 1 stabilization."
            ),
            "🛠️"
        )


# =========================================================
# INSIGHTS TAB
# =========================================================

with insights_tab:

    left_col, right_col = st.columns([1, 1])

    with left_col:

        section_card(
            "Best Current Performer",
            (
                f"The current top-ranked unified model is: {top_model}"
            ),
            "🏆"
        )

        section_card(
            "Strongest Game Coverage",
            (
                f"The current strongest game coverage appears in: {top_game}"
            ),
            "🎲"
        )

        section_card(
            "Random Baseline Tracking",
            (
                "Random baseline models remain intentionally included to "
                "measure whether analytical models outperform randomness."
            ),
            "🎯"
        )

    with right_col:

        section_card(
            "Platform Insight",
            (
                "Phase 1 successfully unified historical ingestion, "
                "prediction generation, backtesting, optimization and reporting."
            ),
            "🚀"
        )

        section_card(
            "Next Evolution",
            (
                "Phase 2 introduces UX improvements, operational control "
                "centers and future football analytics integration."
            ),
            "⚽"
        )

        section_card(
            "Long-Term Direction",
            (
                "The architecture is intentionally modular so additional "
                "prediction engines can plug into the same platform."
            ),
            "🧠"
        )