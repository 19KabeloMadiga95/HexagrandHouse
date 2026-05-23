from datetime import datetime
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

from src.lottery.predictions.ensemble_prediction_engine import (
    export_all_game_ensembles,
)

from src.lottery.reporting.executive_lottery_report import (
    export_executive_report,
)

from src.lottery.reporting.daily_lottery_summary_generator import (
    export_daily_summary,
)


st.set_page_config(
    page_title="Control Center",
    page_icon="⚙️",
    layout="wide",
)

last_refresh_card()


BASE_DIR = Path(__file__).resolve().parents[4]

DATA_DIR = BASE_DIR / "data"
LOTTERY_EXPORTS_DIR = DATA_DIR / "exports"
FOOTBALL_DIR = DATA_DIR / "football"


# =========================================================
# LOTTERY FILES
# =========================================================

MASTER_FILE = DATA_DIR / "master" / "lottery_historical_master.xlsx"

UNIFIED_DASHBOARD = (
    LOTTERY_EXPORTS_DIR
    / "backtesting"
    / "unified_model_performance_dashboard.xlsx"
)

ENSEMBLE_FILE = (
    LOTTERY_EXPORTS_DIR
    / "final_predictions"
    / "all_games_ensemble_predictions.xlsx"
)

EXECUTIVE_REPORT = (
    LOTTERY_EXPORTS_DIR
    / "reporting"
    / "executive_lottery_report.xlsx"
)

DAILY_SUMMARY = (
    LOTTERY_EXPORTS_DIR
    / "reporting"
    / "daily_lottery_summary.xlsx"
)

QUALITY_REPORT = (
    DATA_DIR
    / "processed"
    / "quality"
    / "lottery_quality_report.xlsx"
)

LOG_FILE = (
    DATA_DIR
    / "logs"
    / "daily_lottery_cycle_log.xlsx"
)


# =========================================================
# FOOTBALL FILES
# =========================================================

FOOTBALL_MASTER_ALL = (
    FOOTBALL_DIR
    / "master"
    / "football_master_all_leagues.xlsx"
)

FOOTBALL_FEATURES_ALL = (
    FOOTBALL_DIR
    / "processed"
    / "features"
    / "football_features_all_leagues"
    / "match_features.csv"
)

FOOTBALL_TEAM_FEATURES = (
    FOOTBALL_DIR
    / "processed"
    / "features"
    / "football_features_all_leagues"
    / "team_features_long.csv"
)

FOOTBALL_GOALS_MODEL = (
    FOOTBALL_DIR
    / "exports"
    / "models"
    / "football_goals_model_predictions.xlsx"
)

FOOTBALL_RESULT_MODEL = (
    FOOTBALL_DIR
    / "exports"
    / "models"
    / "football_result_model_predictions.xlsx"
)

FOOTBALL_CORNERS_MODEL = (
    FOOTBALL_DIR
    / "exports"
    / "models"
    / "football_corners_model_predictions.xlsx"
)

FOOTBALL_ENSEMBLE = (
    FOOTBALL_DIR
    / "exports"
    / "predictions"
    / "football_ensemble_predictions.xlsx"
)

FOOTBALL_FIXTURES = (
    FOOTBALL_DIR
    / "master"
    / "football_fixtures.xlsx"
)

FOOTBALL_FIXTURE_PREDICTIONS = (
    FOOTBALL_DIR
    / "exports"
    / "predictions"
    / "football_fixture_predictions.xlsx"
)

FOOTBALL_PERFORMANCE_DASHBOARD = (
    FOOTBALL_DIR
    / "exports"
    / "reporting"
    / "football_model_performance_dashboard.xlsx"
)

FOOTBALL_TOP_PLAYS_REPORT = (
    FOOTBALL_DIR
    / "exports"
    / "reporting"
    / "top_plays_report.xlsx"
)

FOOTBALL_VALUE_BETS = (
    FOOTBALL_DIR
    / "exports"
    / "value"
    / "football_value_bets.xlsx"
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


def clean_dataframe(df):
    if df.empty:
        return df

    df = df.copy()

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str)

    return df


def file_status(path, category):
    exists = path.exists()

    modified = "-"
    size_mb = 0

    if exists:
        modified = datetime.fromtimestamp(
            path.stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M:%S")

        size_mb = round(
            path.stat().st_size / (1024 * 1024),
            2
        )

    return {
        "Category": category,
        "File": path.name,
        "Path": str(path),
        "Exists": exists,
        "LastModified": modified,
        "SizeMB": size_mb,
    }


def dataframe_from_status(file_items):
    rows = []

    for item in file_items:
        rows.append(
            file_status(
                item["Path"],
                item["Category"]
            )
        )

    return pd.DataFrame(rows)


def status_label(value):
    if bool(value):
        return "Ready"

    return "Missing"


def status_icon(value):
    if bool(value):
        return "✅"

    return "❌"


def dataframe_to_csv(df):
    return df.to_csv(
        index=False
    ).encode("utf-8")


# =========================================================
# LOAD DATA
# =========================================================

status_df = dataframe_from_status(
    [
        {"Category": "Lottery", "Path": MASTER_FILE},
        {"Category": "Lottery", "Path": UNIFIED_DASHBOARD},
        {"Category": "Lottery", "Path": ENSEMBLE_FILE},
        {"Category": "Lottery", "Path": EXECUTIVE_REPORT},
        {"Category": "Lottery", "Path": DAILY_SUMMARY},
        {"Category": "Lottery", "Path": QUALITY_REPORT},
        {"Category": "Lottery", "Path": LOG_FILE},

        {"Category": "Football", "Path": FOOTBALL_MASTER_ALL},
        {"Category": "Football", "Path": FOOTBALL_FEATURES_ALL},
        {"Category": "Football", "Path": FOOTBALL_TEAM_FEATURES},
        {"Category": "Football", "Path": FOOTBALL_GOALS_MODEL},
        {"Category": "Football", "Path": FOOTBALL_RESULT_MODEL},
        {"Category": "Football", "Path": FOOTBALL_CORNERS_MODEL},
        {"Category": "Football", "Path": FOOTBALL_ENSEMBLE},
        {"Category": "Football", "Path": FOOTBALL_FIXTURES},
        {"Category": "Football", "Path": FOOTBALL_FIXTURE_PREDICTIONS},
        {"Category": "Football", "Path": FOOTBALL_VALUE_BETS},
        {"Category": "Football", "Path": FOOTBALL_PERFORMANCE_DASHBOARD},
        {"Category": "Football", "Path": FOOTBALL_TOP_PLAYS_REPORT},
    ]
)

runlog_df = clean_dataframe(
    safe_read_excel(
        LOG_FILE,
        "Daily_Cycle_Log"
    )
)


# =========================================================
# HEADER
# =========================================================

hero_banner(
    "Platform Control Center",
    (
        "Operational monitoring layer for lottery and football pipeline health, "
        "exports, reporting, run logs and system readiness."
    ),
    "⚙️"
)

st.divider()


# =========================================================
# KPI SECTION
# =========================================================

files_ready = int(status_df["Exists"].sum())
files_missing = int((~status_df["Exists"]).sum())

lottery_ready = int(
    status_df[
        status_df["Category"] == "Lottery"
    ]["Exists"].sum()
)

football_ready = int(
    status_df[
        status_df["Category"] == "Football"
    ]["Exists"].sum()
)

latest_update = "-"

existing_dates = status_df[
    status_df["LastModified"] != "-"
]

if not existing_dates.empty:
    latest_update = existing_dates["LastModified"].max()

latest_run = "-"
latest_run_status = "-"

if not runlog_df.empty and "RunTimestamp" in runlog_df.columns:
    try:
        runlog_df["RunTimestamp"] = pd.to_datetime(
            runlog_df["RunTimestamp"],
            errors="coerce"
        )

        runlog_df = runlog_df.sort_values(
            by="RunTimestamp",
            ascending=False
        )

        latest_run = str(
            runlog_df.iloc[0]["RunTimestamp"]
        )

        if "Status" in runlog_df.columns:
            latest_run_status = str(
                runlog_df.iloc[0]["Status"]
            )

    except Exception:
        latest_run = "-"

platform_status = (
    "Operational"
    if files_missing == 0
    else "Partial"
)

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    kpi_card(
        "Files Ready",
        files_ready,
        "All tracked outputs",
        "✅"
    )

with k2:
    kpi_card(
        "Files Missing",
        files_missing,
        "Attention required",
        "⚠️"
    )

with k3:
    kpi_card(
        "Lottery Ready",
        lottery_ready,
        "Lottery outputs",
        "🎯"
    )

with k4:
    kpi_card(
        "Football Ready",
        football_ready,
        "Football outputs",
        "⚽"
    )

with k5:
    kpi_card(
        "Platform Status",
        platform_status,
        f"Latest update: {latest_update}",
        "⚙️"
    )


# =========================================================
# TABS
# =========================================================

st.divider()

overview_tab, runlog_tab, outputs_tab, refresh_tab, commands_tab, diagnostics_tab = st.tabs(
    [
        "📊 Overview",
        "📜 Run Log",
        "📋 Outputs",
        "🔁 Refresh Actions",
        "🛠️ Commands",
        "🧪 Diagnostics",
    ]
)


# =========================================================
# OVERVIEW TAB
# =========================================================

with overview_tab:

    left_col, right_col = st.columns([1.3, 1])

    with left_col:

        st.subheader("📋 Critical Output Files")

        display_cols = [
            "Category",
            "File",
            "Exists",
            "LastModified",
            "SizeMB",
        ]

        st.dataframe(
            status_df[display_cols],
            width="stretch",
            height=500
        )

    with right_col:

        section_card(
            "Control Center",
            (
                "This page monitors critical lottery and football outputs, "
                "run logs, processed datasets and prediction files."
            ),
            "⚙️"
        )

        section_card(
            "Current Mode",
            (
                "Safe monitoring mode is active. Heavy jobs should still be "
                "triggered from the terminal."
            ),
            "🛡️"
        )

        section_card(
            "Football Integration",
            (
                "Football ingestion, features, models, fixtures, predictions "
                "and reporting outputs are now tracked here."
            ),
            "⚽"
        )


# =========================================================
# RUN LOG TAB
# =========================================================

with runlog_tab:

    st.subheader("📜 Daily Lottery Cycle Run Log")

    if runlog_df.empty:

        st.warning(
            "No daily cycle run log found yet."
        )

        section_card(
            "Run Log Missing",
            (
                "Run the daily lottery cycle once to generate the log file."
            ),
            "📜"
        )

    else:

        log_df = runlog_df.copy()

        if "RunTimestamp" in log_df.columns:
            log_df["RunTimestamp"] = pd.to_datetime(
                log_df["RunTimestamp"],
                errors="coerce"
            )

            log_df = log_df.sort_values(
                by="RunTimestamp",
                ascending=False
            )

        success_count = (
            int((log_df["Status"] == "Success").sum())
            if "Status" in log_df.columns
            else 0
        )

        failed_count = (
            int((log_df["Status"] == "Failed").sum())
            if "Status" in log_df.columns
            else 0
        )

        latest_log_time = "-"

        if "RunTimestamp" in log_df.columns and not log_df.empty:
            latest_log_time = str(
                log_df.iloc[0]["RunTimestamp"]
            )

        avg_duration = "-"

        if "DurationSeconds" in log_df.columns:
            duration_series = pd.to_numeric(
                log_df["DurationSeconds"],
                errors="coerce"
            ).dropna()

            if not duration_series.empty:
                avg_duration = round(
                    duration_series.mean(),
                    2
                )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            kpi_card(
                "Successful Steps",
                success_count,
                "Logged successes",
                "✅"
            )

        with c2:
            kpi_card(
                "Failed Steps",
                failed_count,
                "Logged failures",
                "❌"
            )

        with c3:
            kpi_card(
                "Average Duration",
                avg_duration,
                "Seconds per step",
                "⏱️"
            )

        with c4:
            kpi_card(
                "Latest Log Entry",
                latest_log_time,
                "Most recent step",
                "🕒"
            )

        st.divider()

        log_left, log_right = st.columns([1.4, 1])

        with log_left:

            st.subheader("📋 Full Run Log")

            st.dataframe(
                log_df,
                width="stretch",
                height=560
            )

        with log_right:

            st.subheader("📈 Step Duration")

            if "StepName" in log_df.columns and "DurationSeconds" in log_df.columns:

                duration_chart = log_df.copy()

                duration_chart["DurationSeconds"] = pd.to_numeric(
                    duration_chart["DurationSeconds"],
                    errors="coerce"
                )

                duration_chart = duration_chart.dropna(
                    subset=[
                        "StepName",
                        "DurationSeconds",
                    ]
                )

                duration_chart = duration_chart.sort_values(
                    by="DurationSeconds",
                    ascending=True
                ).tail(15)

                if not duration_chart.empty:
                    plot_bar_chart(
                        df=duration_chart,
                        x_col="StepName",
                        y_col="DurationSeconds",
                        title="Slowest Logged Steps",
                        height=420
                    )

            st.divider()

            failed_df = pd.DataFrame()

            if "Status" in log_df.columns:
                failed_df = log_df[
                    log_df["Status"] == "Failed"
                ].copy()

            if failed_df.empty:
                section_card(
                    "Failure Status",
                    "No failed steps found in the current run log.",
                    "✅"
                )

            else:
                section_card(
                    "Failure Status",
                    (
                        f"{len(failed_df)} failed step(s) found. "
                        "Review the error messages in the log table."
                    ),
                    "⚠️"
                )

                failed_cols = [
                    col for col in [
                        "RunTimestamp",
                        "StepName",
                        "ErrorMessage",
                    ]
                    if col in failed_df.columns
                ]

                st.dataframe(
                    failed_df[failed_cols],
                    width="stretch",
                    height=260
                )


# =========================================================
# OUTPUTS TAB
# =========================================================

with outputs_tab:

    st.subheader("📋 Output File Status")

    status_display = status_df.copy()

    status_display["Status"] = status_display["Exists"].apply(
        status_label
    )

    status_display["Icon"] = status_display["Exists"].apply(
        status_icon
    )

    category_filter = st.selectbox(
        "Filter category",
        [
            "All",
            "Lottery",
            "Football",
        ]
    )

    if category_filter != "All":
        status_display = status_display[
            status_display["Category"] == category_filter
        ]

    display_cols = [
        "Icon",
        "Category",
        "File",
        "Status",
        "LastModified",
        "SizeMB",
        "Path",
    ]

    st.dataframe(
        status_display[display_cols],
        width="stretch",
        height=560
    )

    st.divider()

    if not status_display.empty:
        csv = dataframe_to_csv(
            status_display[display_cols]
        )

        st.download_button(
            label="Download Output Status",
            data=csv,
            file_name="platform_output_status.csv",
            mime="text/csv"
        )


# =========================================================
# REFRESH TAB
# =========================================================

with refresh_tab:

    st.subheader("🔁 Safe Refresh Actions")

    section_card(
        "Safe Actions Only",
        (
            "These refresh actions are lightweight operations designed "
            "to avoid freezing the Streamlit frontend."
        ),
        "🛡️"
    )

    st.divider()

    refresh_col1, refresh_col2, refresh_col3 = st.columns(3)

    with refresh_col1:

        st.markdown("### 🧠 Final Ensembles")

        st.caption(
            "Regenerates lottery final ensemble outputs."
        )

        if st.button(
            "Refresh Final Ensembles",
            width="stretch"
        ):

            try:
                with st.spinner(
                    "Refreshing final ensembles..."
                ):
                    export_all_game_ensembles()

                st.success(
                    "Final ensemble predictions refreshed successfully."
                )

            except Exception as e:
                st.error(
                    f"Failed to refresh ensembles: {e}"
                )

    with refresh_col2:

        st.markdown("### 📋 Executive Report")

        st.caption(
            "Regenerates lottery executive reporting outputs."
        )

        if st.button(
            "Refresh Executive Report",
            width="stretch"
        ):

            try:
                with st.spinner(
                    "Refreshing executive report..."
                ):
                    export_executive_report()

                st.success(
                    "Executive report refreshed successfully."
                )

            except Exception as e:
                st.error(
                    f"Failed to refresh executive report: {e}"
                )

    with refresh_col3:

        st.markdown("### ☀️ Daily Summary")

        st.caption(
            "Regenerates lottery daily operational summary."
        )

        if st.button(
            "Refresh Daily Summary",
            width="stretch"
        ):

            try:
                with st.spinner(
                    "Refreshing daily summary..."
                ):
                    export_daily_summary()

                st.success(
                    "Daily summary refreshed successfully."
                )

            except Exception as e:
                st.error(
                    f"Failed to refresh daily summary: {e}"
                )

    st.divider()

    section_card(
        "Football Refresh Notice",
        (
            "Football jobs are currently listed as terminal commands because they "
            "are heavier and include ingestion, feature generation and model exports."
        ),
        "⚽"
    )


# =========================================================
# COMMANDS TAB
# =========================================================

with commands_tab:

    st.subheader("🛠️ Platform Commands")

    lottery_commands_tab, football_commands_tab = st.tabs(
        [
            "🎯 Lottery Commands",
            "⚽ Football Commands",
        ]
    )

    with lottery_commands_tab:

        section_card(
            "Daily Lottery Pipeline",
            (
                "Run the full lottery analytics cycle from the terminal."
            ),
            "▶️"
        )

        st.code(
            "python -m src.lottery.automation.run_daily_lottery_cycle",
            language="powershell"
        )

        st.divider()

        section_card(
            "Streamlit Frontend",
            (
                "Launch the frontend dashboard locally."
            ),
            "🖥️"
        )

        st.code(
            "python -m streamlit run src/lottery/frontend/streamlit_app.py",
            language="powershell"
        )

        st.divider()

        section_card(
            "Run Final Ensemble Only",
            (
                "Use this when base predictions and optimizers already exist."
            ),
            "🧠"
        )

        st.code(
            "python -m src.lottery.predictions.ensemble_prediction_engine",
            language="powershell"
        )

        st.divider()

        section_card(
            "Regenerate Reports Only",
            (
                "Refresh lottery reporting files."
            ),
            "📋"
        )

        st.code(
            "python -m src.lottery.reporting.executive_lottery_report\n"
            "python -m src.lottery.reporting.daily_lottery_summary_generator",
            language="powershell"
        )

    with football_commands_tab:

        section_card(
            "Full Football Build Order",
            (
                "Run these commands in order when refreshing the full football module."
            ),
            "⚽"
        )

        st.code(
            "python -m src.football.data_ingestion.build_UKDATA27_football_master_dataset\n"
            "python -m src.football.features.build_football_features\n"
            "python -m src.football.models.goals_model\n"
            "python -m src.football.models.result_model\n"
            "python -m src.football.models.corners_model\n"
            "python -m src.football.models.ensemble_engine\n"
            "python -m src.football.data_ingestion.build_football_fixtures\n"
            "python -m src.football.predictions.predict_fixtures\n"
            "python -m src.football.value.value_bet_engine\n"
            "python -m src.football.reporting.football_model_performance_dashboard\n"
            "python -m src.football.reporting.top_plays_report",
            language="powershell"
        )

        st.divider()

        section_card(
            "Daily Football Prediction Refresh",
            (
                "Use this shorter set after the historical master and features already exist."
            ),
            "📅"
        )

        st.code(
            "python -m src.football.data_ingestion.build_football_fixtures\n"
            "python -m src.football.predictions.predict_fixtures\n"
            "python -m src.football.value.value_bet_engine\n"
            "python -m src.football.reporting.football_model_performance_dashboard\n"
            "python -m src.football.reporting.top_plays_report",
            language="powershell"
        )

        st.divider()

        section_card(
            "Historical Football Model Refresh",
            (
                "Use this when you want to rebuild model outputs after feature updates."
            ),
            "🧠"
        )

        st.code(
            "python -m src.football.features.build_football_features\n"
            "python -m src.football.models.goals_model\n"
            "python -m src.football.models.result_model\n"
            "python -m src.football.models.corners_model\n"
            "python -m src.football.models.ensemble_engine",
            language="powershell"
        )


# =========================================================
# DIAGNOSTICS TAB
# =========================================================

with diagnostics_tab:

    diagnostics_col1, diagnostics_col2 = st.columns([1.2, 1])

    with diagnostics_col1:

        st.subheader("🧪 Dataset Diagnostics")

        diagnostic_rows = []

        diagnostic_map = [
            ("Lottery", "Master Historical", MASTER_FILE),
            ("Lottery", "Unified Dashboard", UNIFIED_DASHBOARD),
            ("Lottery", "Final Ensembles", ENSEMBLE_FILE),
            ("Lottery", "Executive Report", EXECUTIVE_REPORT),
            ("Lottery", "Daily Summary", DAILY_SUMMARY),
            ("Lottery", "Quality Report", QUALITY_REPORT),
            ("Lottery", "Cycle Log", LOG_FILE),

            ("Football", "Master All Leagues", FOOTBALL_MASTER_ALL),
            ("Football", "Match Features", FOOTBALL_FEATURES_ALL),
            ("Football", "Team Features", FOOTBALL_TEAM_FEATURES),
            ("Football", "Goals Model", FOOTBALL_GOALS_MODEL),
            ("Football", "Result Model", FOOTBALL_RESULT_MODEL),
            ("Football", "Corners Model", FOOTBALL_CORNERS_MODEL),
            ("Football", "Historical Ensemble", FOOTBALL_ENSEMBLE),
            ("Football", "Fixtures", FOOTBALL_FIXTURES),
            ("Football", "Fixture Predictions", FOOTBALL_FIXTURE_PREDICTIONS),
            ("Football", "Value Bets", FOOTBALL_VALUE_BETS),
            ("Football", "Performance Dashboard", FOOTBALL_PERFORMANCE_DASHBOARD),
            ("Football", "Top Plays Report", FOOTBALL_TOP_PLAYS_REPORT),
        ]

        for category, dataset_name, dataset_path in diagnostic_map:
            diagnostic_rows.append(
                {
                    "Category": category,
                    "Dataset": dataset_name,
                    "Status": (
                        "Ready"
                        if dataset_path.exists()
                        else "Missing"
                    ),
                    "Path": str(dataset_path),
                }
            )

        diagnostics_df = pd.DataFrame(
            diagnostic_rows
        )

        st.dataframe(
            diagnostics_df,
            width="stretch",
            height=520
        )

    with diagnostics_col2:

        st.subheader("💡 Platform Insights")

        if files_missing == 0:
            section_card(
                "Healthy State",
                (
                    "All tracked platform outputs currently exist. "
                    "The system is ready for analysis."
                ),
                "✅"
            )

        else:
            section_card(
                "Partial State",
                (
                    f"{files_missing} tracked output file(s) are missing. "
                    "Review the Outputs tab."
                ),
                "⚠️"
            )

        section_card(
            "Common Failure Points",
            (
                "Most operational failures occur during ingestion, file writing, "
                "missing source datasets, locked Excel files or long-running backtests."
            ),
            "⚠️"
        )

        section_card(
            "Football Notes",
            (
                "Corners are only valid where source data includes corners. "
                "Tier 3 leagues may have goals/results coverage without corners."
            ),
            "⚽"
        )

        section_card(
            "Scalability Direction",
            (
                "This operational layer prepares the platform for future "
                "database integration, cloud deployment and scheduled jobs."
            ),
            "☁️"
        )


st.divider()

section_card(
    "Operational Notes",
    (
        "The Control Center provides visibility into platform health without "
        "directly executing heavy processes from the frontend. This prevents "
        "UI freezes while keeping operations observable."
    ),
    "📌"
)