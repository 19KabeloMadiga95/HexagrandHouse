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
    page_title="Football Model Performance",
    page_icon="🧠",
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


def get_kpi_value(kpi_df, kpi_name, default="-"):
    if kpi_df.empty:
        return default

    if "KPI" not in kpi_df.columns or "Value" not in kpi_df.columns:
        return default

    match = kpi_df[
        kpi_df["KPI"] == kpi_name
    ]

    if match.empty:
        return default

    return match.iloc[0]["Value"]


kpi_df = safe_read_excel(
    PERFORMANCE_DASHBOARD,
    "High_Level_KPIs"
)

dashboard_df = safe_read_excel(
    PERFORMANCE_DASHBOARD,
    "Dashboard_Summary"
)

league_df = safe_read_excel(
    PERFORMANCE_DASHBOARD,
    "League_Performance"
)

file_status_df = safe_read_excel(
    PERFORMANCE_DASHBOARD,
    "File_Status"
)


hero_banner(
    "Football Model Performance",
    (
        "Model performance control layer for goals, corners, results, "
        "historical ensembles and future fixture predictions."
    ),
    "🧠"
)

st.divider()


if kpi_df.empty and dashboard_df.empty:
    st.warning(
        "No football performance dashboard found. Run the reporting script first."
    )

    st.code(
        "python -m src.football.reporting.football_model_performance_dashboard",
        language="powershell"
    )

    st.stop()


k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    kpi_card(
        "Goals Rows",
        get_kpi_value(
            kpi_df,
            "Goals Prediction Rows"
        ),
        "Historical scored rows",
        "⚽"
    )

with k2:
    kpi_card(
        "Corners Rows",
        get_kpi_value(
            kpi_df,
            "Corners Prediction Rows"
        ),
        "Rows with corner data",
        "🚩"
    )

with k3:
    kpi_card(
        "Result Rows",
        get_kpi_value(
            kpi_df,
            "Result Prediction Rows"
        ),
        "Three-way result model",
        "🎯"
    )

with k4:
    kpi_card(
        "Fixture Rows",
        get_kpi_value(
            kpi_df,
            "Future Fixture Prediction Rows"
        ),
        "Upcoming predictions",
        "📅"
    )

with k5:
    kpi_card(
        "Future Elite",
        get_kpi_value(
            kpi_df,
            "Future Elite Predictions"
        ),
        "High-confidence fixtures",
        "🔥"
    )


st.divider()


tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Dashboard Summary",
        "🌍 League Performance",
        "📈 Charts",
        "🧪 File Status",
    ]
)


with tab1:

    st.subheader("📊 Model Dashboard Summary")

    if dashboard_df.empty:
        st.warning("No dashboard summary available.")

    else:
        st.dataframe(
            dashboard_df,
            width="stretch",
            height=620
        )

    st.divider()

    st.subheader("📌 High-Level KPIs")

    if kpi_df.empty:
        st.warning("No KPI sheet available.")

    else:
        st.dataframe(
            kpi_df,
            width="stretch",
            height=420
        )


with tab2:

    st.subheader("🌍 League Performance")

    if league_df.empty:
        st.warning("No league performance data available.")

    else:
        model_areas = ["All"]

        if "ModelArea" in league_df.columns:
            model_areas += sorted(
                league_df["ModelArea"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        selected_model_area = st.selectbox(
            "Model Area",
            model_areas
        )

        filtered_league_df = league_df.copy()

        if (
            selected_model_area != "All"
            and "ModelArea" in filtered_league_df.columns
        ):
            filtered_league_df = filtered_league_df[
                filtered_league_df["ModelArea"] == selected_model_area
            ]

        st.dataframe(
            filtered_league_df,
            width="stretch",
            height=700
        )


with tab3:

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:

        st.subheader("📈 Prediction Accuracy by Model")

        if (
            not dashboard_df.empty
            and "PredictionAccuracy" in dashboard_df.columns
            and "Metric" in dashboard_df.columns
        ):
            accuracy_df = dashboard_df[
                dashboard_df["PredictionAccuracy"].notna()
            ].copy()

            if not accuracy_df.empty:
                accuracy_df["PredictionAccuracy"] = pd.to_numeric(
                    accuracy_df["PredictionAccuracy"],
                    errors="coerce"
                )

                accuracy_df = accuracy_df.sort_values(
                    by="PredictionAccuracy",
                    ascending=False
                )

                plot_bar_chart(
                    df=accuracy_df,
                    x_col="Metric",
                    y_col="PredictionAccuracy",
                    title="Model Accuracy Comparison",
                    height=430
                )

            else:
                st.info("No accuracy metrics available.")

    with chart_col2:

        st.subheader("🔥 File Readiness")

        if (
            not file_status_df.empty
            and "FileType" in file_status_df.columns
            and "Exists" in file_status_df.columns
        ):
            status_chart = file_status_df.copy()

            status_chart["Ready"] = status_chart["Exists"].astype(int)

            plot_bar_chart(
                df=status_chart,
                x_col="FileType",
                y_col="Ready",
                title="Model File Status",
                height=430
            )

    st.divider()

    st.subheader("🌍 League Confidence Extract")

    if (
        not league_df.empty
        and "AvgEnsembleConfidence" in league_df.columns
        and "League" in league_df.columns
    ):
        conf_df = league_df[
            league_df["AvgEnsembleConfidence"].notna()
        ].copy()

        conf_df["AvgEnsembleConfidence"] = pd.to_numeric(
            conf_df["AvgEnsembleConfidence"],
            errors="coerce"
        )

        conf_df = conf_df.sort_values(
            by="AvgEnsembleConfidence",
            ascending=False
        ).head(20)

        plot_bar_chart(
            df=conf_df,
            x_col="League",
            y_col="AvgEnsembleConfidence",
            title="Top Leagues by Ensemble Confidence",
            height=500
        )

    else:
        st.info("No ensemble confidence data available.")


with tab4:

    st.subheader("🧪 Football Model File Status")

    if file_status_df.empty:
        st.warning("No file status data available.")

    else:
        st.dataframe(
            file_status_df,
            width="stretch",
            height=520
        )

    st.divider()

    section_card(
        "Refresh Command",
        (
            "Use this command after rerunning any football model to refresh "
            "the performance dashboard output."
        ),
        "🛠️"
    )

    st.code(
        "python -m src.football.reporting.football_model_performance_dashboard",
        language="powershell"
    )


st.divider()

section_card(
    "Model Governance Note",
    (
        "This page is the football model monitoring layer. It helps identify which "
        "models are producing useful signals, which leagues perform best, and whether "
        "all required football output files are available."
    ),
    "📌"
)