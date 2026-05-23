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

from lottery.frontend.components.charts import (
    plot_bar_chart,
)

from lottery.frontend.components.lottery_prediction_card import (
    render_lottery_prediction_cards,
)


st.set_page_config(
    page_title="Lottery Intelligence",
    page_icon="🎲",
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

RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "master"
    / "lottery_historical_master.xlsx"
)

PREDICTIONS_FILE = (
    BASE_DIR
    / "data"
    / "exports"
    / "final_predictions"
    / "all_games_ensemble_predictions.xlsx"
)

MODEL_FILE = (
    BASE_DIR
    / "data"
    / "exports"
    / "backtesting"
    / "unified_model_performance_dashboard.xlsx"
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


def clean_text(value):
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip()

    if value.lower() in ["nan", "none", "nat"]:
        return ""

    return value


def add_game_display_column(df):
    if df.empty:
        return df

    df = df.copy()

    game_display_values = []

    for _, row in df.iterrows():
        game_family = clean_text(row.get("GameFamily"))
        game_name = clean_text(row.get("GameName"))
        draw_type = clean_text(row.get("DrawType"))

        base_name = game_name or game_family or "Unknown"

        if base_name.upper() == "UK49S":
            if draw_type:
                game_display = f"UK49s {draw_type}"
            else:
                game_display = "UK49s"

        elif game_family.upper() == "UK49S":
            if draw_type:
                game_display = f"UK49s {draw_type}"
            else:
                game_display = base_name

        else:
            game_display = base_name

        game_display_values.append(
            game_display.strip()
        )

    df["GameDisplay"] = game_display_values

    return df


def filter_by_game(df, selected_game):
    if df.empty or selected_game == "All":
        return df

    if "GameDisplay" not in df.columns:
        df = add_game_display_column(df)

    return df[
        df["GameDisplay"].astype(str) == selected_game
    ].copy()


def get_latest_results(df, limit=10):
    if df.empty:
        return df

    if "DrawDate" not in df.columns:
        return df.head(limit)

    temp = df.copy()

    temp["DrawDate"] = pd.to_datetime(
        temp["DrawDate"],
        errors="coerce"
    )

    temp = temp.sort_values(
        by="DrawDate",
        ascending=False
    )

    return temp.head(limit)


results_df = safe_read_excel(
    RESULTS_FILE
)

predictions_df = safe_read_excel(
    PREDICTIONS_FILE,
    "All_Ensemble_Predictions"
)

if predictions_df.empty:
    predictions_df = safe_read_excel(
        PREDICTIONS_FILE
    )

models_df = safe_read_excel(
    MODEL_FILE,
    "Unified_Leaderboard"
)

if models_df.empty:
    models_df = safe_read_excel(
        MODEL_FILE
    )


results_df = add_game_display_column(results_df)
predictions_df = add_game_display_column(predictions_df)
models_df = add_game_display_column(models_df)


st.markdown(
    """<div class="hgh-premium-hero-small"><div class="hgh-hero-kicker">LOTTERY INTELLIGENCE</div><h1 class="hgh-hero-title-small">Smart Lottery Analytics</h1><p class="hgh-hero-subtitle-small">Choose a lottery game and view curated predictions, latest results and model intelligence in one clean view.</p></div>""",
    unsafe_allow_html=True
)

st.divider()


game_options = ["All"]

for df in [
    predictions_df,
    results_df,
    models_df,
]:
    if not df.empty and "GameDisplay" in df.columns:
        game_options.extend(
            df["GameDisplay"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

game_options = ["All"] + sorted(
    list(
        set(
            [
                game for game in game_options
                if game != "All"
            ]
        )
    )
)

selected_game = st.selectbox(
    "🎲 Select Lottery Game",
    game_options
)


filtered_predictions_df = filter_by_game(
    predictions_df,
    selected_game
)

filtered_results_df = filter_by_game(
    results_df,
    selected_game
)

filtered_models_df = filter_by_game(
    models_df,
    selected_game
)

latest_results_df = get_latest_results(
    filtered_results_df,
    12
)


prediction_rows = len(filtered_predictions_df)
result_rows = len(filtered_results_df)

latest_draw = "-"

if not latest_results_df.empty and "DrawDate" in latest_results_df.columns:
    latest_draw_value = pd.to_datetime(
        latest_results_df.iloc[0]["DrawDate"],
        errors="coerce"
    )

    if not pd.isna(latest_draw_value):
        latest_draw = latest_draw_value.strftime(
            "%Y-%m-%d"
        )


k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card(
        "Selected Game",
        selected_game,
        "Current view",
        "🎲"
    )

with k2:
    kpi_card(
        "Predictions",
        prediction_rows,
        "Generated selections",
        "🧠"
    )

with k3:
    kpi_card(
        "Latest Draw",
        latest_draw,
        "Newest result",
        "📅"
    )

with k4:
    kpi_card(
        "Historical Rows",
        result_rows,
        "Results available",
        "📚"
    )


st.divider()


tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🎯 Prediction Cards",
        "📋 Prediction Table",
        "📊 Results",
        "🏆 Models",
    ]
)


with tab1:
    st.markdown("## 🎯 Curated Prediction Cards")

    if filtered_predictions_df.empty:
        st.warning(
            "No prediction data available for the selected game."
        )
    else:
        render_lottery_prediction_cards(
            filtered_predictions_df,
            max_cards=12
        )

    section_card(
        "How To Read These Cards",
        (
            "Each card represents a generated lottery selection. "
            "The number balls show the selection, while the supporting metrics "
            "show balance indicators such as high/low split, odd/even split and total sum."
        ),
        "🎲"
    )


with tab2:
    st.markdown("## 📋 Prediction Table")

    if filtered_predictions_df.empty:
        st.warning(
            "No prediction data available for the selected game."
        )
    else:
        display_cols = [
            col for col in [
                "GameDisplay",
                "GameFamily",
                "GameName",
                "DrawType",
                "PredictionRank",
                "Rank",
                "N1",
                "N2",
                "N3",
                "N4",
                "N5",
                "N6",
                "Bonus",
                "RegularSum",
                "HighCount",
                "LowCount",
                "OddCount",
                "EvenCount",
                "ConfidenceScore",
                "ModelName",
            ]
            if col in filtered_predictions_df.columns
        ]

        st.dataframe(
            filtered_predictions_df[display_cols].head(50),
            use_container_width=True,
            height=560
        )


with tab3:
    st.markdown("## 📊 Latest Lottery Results")

    if latest_results_df.empty:
        st.warning(
            "No results data available for the selected game."
        )
    else:
        display_cols = [
            col for col in [
                "GameDisplay",
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
            if col in latest_results_df.columns
        ]

        st.dataframe(
            latest_results_df[display_cols],
            use_container_width=True,
            height=520
        )

    if not filtered_results_df.empty and "GameDisplay" in filtered_results_df.columns:
        chart_df = (
            filtered_results_df["GameDisplay"]
            .value_counts()
            .reset_index()
        )

        chart_df.columns = [
            "Game",
            "Count",
        ]

        st.markdown("### 📈 Result Coverage")

        plot_bar_chart(
            chart_df,
            x_col="Game",
            y_col="Count",
            title="Latest Results by Game"
        )


with tab4:
    st.markdown("## 🏆 Model Intelligence")

    if filtered_models_df.empty:
        st.warning(
            "No model data available for the selected game."
        )
    else:
        display_cols = [
            col for col in [
                "GameDisplay",
                "GameFamily",
                "GameName",
                "DrawType",
                "ModelName",
                "Rank",
                "UnifiedRank",
                "AverageBestRegularMatch_PerDraw",
                "DrawsTested",
            ]
            if col in filtered_models_df.columns
        ]

        st.dataframe(
            filtered_models_df[display_cols].head(30),
            use_container_width=True,
            height=560
        )

    section_card(
        "Unified Model System",
        (
            "The platform compares multiple lottery prediction strategies "
            "across supported games to identify stronger historical performers."
        ),
        "🏆"
    )


st.divider()

st.markdown(
    """<div class="hgh-footer-note">Lottery predictions are probability-based analytical outputs and should be used responsibly.</div>""",
    unsafe_allow_html=True
)