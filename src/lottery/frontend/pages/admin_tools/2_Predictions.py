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
    page_title="Lottery Predictions",
    page_icon="🎯",
    layout="wide",
)

last_refresh_card()


BASE_DIR = Path(__file__).resolve().parents[4]

PREDICTIONS_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "predictions"
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


prediction_files = {
    "PowerBall": (
        PREDICTIONS_DIR / "powerball_predictions.xlsx",
        "PowerBall_Predictions",
    ),
    "Lotto": (
        PREDICTIONS_DIR / "lotto_predictions.xlsx",
        "Lotto_Predictions",
    ),
    "Daily Lotto": (
        PREDICTIONS_DIR / "daily_lotto_predictions.xlsx",
        "Daily_Lotto_Predictions",
    ),
    "UK49s": (
        PREDICTIONS_DIR / "uk49s_predictions.xlsx",
        "UK49s_Predictions",
    ),
}


hero_banner(
    "Lottery Predictions",
    (
        "Base predictions, final ensemble rankings and optimized "
        "game selections across all supported lottery types."
    ),
    "🎯"
)

st.divider()


k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card(
        "Supported Games",
        4,
        "Prediction-ready",
        "🎲"
    )

with k2:
    kpi_card(
        "Prediction Models",
        5,
        "Core engines",
        "🧠"
    )

with k3:
    kpi_card(
        "Optimization",
        "Enabled",
        "Genetic + Ensemble",
        "🧬"
    )

with k4:
    kpi_card(
        "Prediction Status",
        "Live",
        "Pipeline operational",
        "✅"
    )


st.divider()

base_tab, ensemble_tab, export_tab, notes_tab = st.tabs(
    [
        "🎲 Base Predictions",
        "🧠 Final Ensembles",
        "⬇️ Exports",
        "📋 Notes",
    ]
)


# =========================================================
# LOAD SHARED ENSEMBLE DATA
# =========================================================

ensemble_df = clean_dataframe(
    safe_read_excel(
        ENSEMBLE_FILE,
        "All_Ensemble_Predictions"
    )
)


# =========================================================
# BASE PREDICTIONS TAB
# =========================================================

with base_tab:

    selected_game = st.selectbox(
        "Select Game",
        [
            "PowerBall",
            "Lotto",
            "Daily Lotto",
            "UK49s",
        ]
    )

    file_path, sheet_name = prediction_files[selected_game]

    prediction_df = clean_dataframe(
        safe_read_excel(
            file_path,
            sheet_name
        )
    )

    left_col, right_col = st.columns([1.4, 1])

    with left_col:
        st.subheader(
            f"🎲 {selected_game} Base Predictions"
        )

        if prediction_df.empty:
            st.warning("No predictions found.")

        else:
            st.dataframe(
                prediction_df,
                width="stretch",
                height=500
            )

    with right_col:
        st.subheader("📈 Prediction Analytics")

        score_cols = [
            "PredictionScore",
            "FitnessScore",
            "EnsembleScore",
            "RegularSum",
        ]

        available_score_col = None

        for col in score_cols:
            if col in prediction_df.columns:
                available_score_col = col
                break

        if available_score_col and not prediction_df.empty:
            chart_df = prediction_df.copy()

            chart_df[available_score_col] = pd.to_numeric(
                chart_df[available_score_col],
                errors="coerce"
            )

            chart_df = chart_df.dropna(
                subset=[available_score_col]
            )

            if not chart_df.empty:
                chart_df = chart_df.reset_index()

                plot_bar_chart(
                    df=chart_df,
                    x_col="index",
                    y_col=available_score_col,
                    title=f"{selected_game} {available_score_col}",
                    height=420
                )

        st.divider()

        section_card(
            f"{selected_game} Engine",
            (
                "Base predictions are generated using statistical modelling, "
                "weighting systems, diversity controls and optimization layers."
            ),
            "🎯"
        )


# =========================================================
# FINAL ENSEMBLE TAB
# =========================================================

with ensemble_tab:

    ensemble_left, ensemble_right = st.columns([1.4, 1])

    with ensemble_left:
        st.subheader("🧠 Final Ensemble Predictions")

        if ensemble_df.empty:
            st.warning("No final ensemble predictions found.")

        else:
            game_filter = st.selectbox(
                "Filter Ensemble by Game",
                ["All"] + sorted(
                    ensemble_df["GameFamily"].dropna().unique().tolist()
                )
                if "GameFamily" in ensemble_df.columns
                else ["All"]
            )

            filtered_ensemble_df = ensemble_df.copy()

            if (
                game_filter != "All"
                and "GameFamily" in filtered_ensemble_df.columns
            ):
                filtered_ensemble_df = filtered_ensemble_df[
                    filtered_ensemble_df["GameFamily"] == game_filter
                ]

            st.dataframe(
                filtered_ensemble_df,
                width="stretch",
                height=500
            )

    with ensemble_right:
        st.subheader("📈 Ensemble Score Distribution")

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

            if (
                "GameFamily" in chart_df.columns
                and "EnsembleRank" in chart_df.columns
            ):
                chart_df["ChartLabel"] = (
                    chart_df["GameFamily"].astype(str)
                    + " Rank "
                    + chart_df["EnsembleRank"].astype(str)
                )
            else:
                chart_df["ChartLabel"] = chart_df.index.astype(str)

            if not chart_df.empty:
                chart_df = chart_df.sort_values(
                    by="EnsembleScore",
                    ascending=True
                ).tail(15)

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
                "The ensemble engine combines base prediction outputs, "
                "genetic optimizer results, model agreement, ranking strength "
                "and diversity filters into one final selection layer."
            ),
            "🧠"
        )


# =========================================================
# EXPORTS TAB
# =========================================================

with export_tab:

    st.subheader("⬇️ Export Predictions")

    export_col1, export_col2 = st.columns(2)

    with export_col1:
        st.markdown("### Base Predictions")

        export_game = st.selectbox(
            "Select Base Prediction Export",
            [
                "PowerBall",
                "Lotto",
                "Daily Lotto",
                "UK49s",
            ],
            key="base_export_game"
        )

        export_file_path, export_sheet_name = prediction_files[export_game]

        export_prediction_df = clean_dataframe(
            safe_read_excel(
                export_file_path,
                export_sheet_name
            )
        )

        if export_prediction_df.empty:
            st.warning("No base prediction export available.")

        else:
            csv = export_prediction_df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label=f"Download {export_game} Predictions",
                data=csv,
                file_name=f"{export_game.lower().replace(' ', '_')}_predictions.csv",
                mime="text/csv"
            )

    with export_col2:
        st.markdown("### Final Ensemble Predictions")

        if ensemble_df.empty:
            st.warning("No final ensemble export available.")

        else:
            csv = ensemble_df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="Download Final Ensemble Predictions",
                data=csv,
                file_name="final_ensemble_predictions.csv",
                mime="text/csv"
            )


# =========================================================
# NOTES TAB
# =========================================================

with notes_tab:

    section_card(
        "Prediction Notes",
        (
            "Lottery systems remain fundamentally random. "
            "Predictions generated by HexagrandHouse are analytical, "
            "probability-based outputs and not guaranteed outcomes."
        ),
        "📋"
    )

    section_card(
        "Base Predictions",
        (
            "Base prediction files are produced independently for each game. "
            "They provide the first prediction layer before optimization and "
            "ensemble scoring."
        ),
        "🎲"
    )

    section_card(
        "Final Ensembles",
        (
            "Final ensemble predictions combine base model output, genetic "
            "optimizer output, model agreement, rank strength and diversity "
            "controls."
        ),
        "🧠"
    )