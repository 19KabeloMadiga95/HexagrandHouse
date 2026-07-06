from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.data.database import get_database_summary, table_exists
from src.data.sqlite_store import create_indexes, read_sqlite_table, replace_sqlite_table
from src.lottery.reporting.daily_lottery_summary_generator import (
    build_latest_results as build_daily_latest_results,
    build_top_predictions,
    load_base_predictions,
    load_master_data,
)


# =========================================================
# SQLITE-FIRST EXECUTIVE LOTTERY REPORT
# =========================================================

EXECUTIVE_SUMMARY_TABLE = "lottery_executive_summary"
EXECUTIVE_LATEST_RESULTS_TABLE = "lottery_executive_latest_results"
EXECUTIVE_COVERAGE_TABLE = "lottery_executive_coverage_summary"
EXECUTIVE_PLATFORM_STATUS_TABLE = "lottery_executive_platform_status"
EXECUTIVE_STATISTICS_TABLE = "lottery_executive_statistical_insights"
EXECUTIVE_TOP_SIGNALS_TABLE = "lottery_executive_top_signals"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_df(table_name: str) -> pd.DataFrame:
    if not table_exists(table_name):
        return pd.DataFrame()
    return read_sqlite_table(table_name)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    return df.copy().dropna(how="all").reset_index(drop=True)


# Backward-compatible loader names.
def load_unified_leaderboard() -> pd.DataFrame:
    return _safe_df("lottery_model_leaderboard")


def load_best_by_game() -> pd.DataFrame:
    return _safe_df("lottery_model_best_by_game")


def load_vs_random() -> pd.DataFrame:
    return _safe_df("lottery_model_vs_random")


def load_game_summary() -> pd.DataFrame:
    return _safe_df("lottery_model_game_summary")


def load_final_ensembles() -> pd.DataFrame:
    return load_base_predictions()


# =========================================================
# BUILDERS
# =========================================================


def build_executive_summary(
    master_df: pd.DataFrame | None = None,
    predictions_df: pd.DataFrame | None = None,
    leaderboard_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    history = load_master_data() if master_df is None else master_df.copy()
    predictions = load_base_predictions() if predictions_df is None else predictions_df.copy()
    leaderboard = load_unified_leaderboard() if leaderboard_df is None else leaderboard_df.copy()

    avg_conf = round(float(predictions["ConfidenceScore"].mean()), 2) if not predictions.empty and "ConfidenceScore" in predictions.columns else 0
    best_conf = round(float(predictions["ConfidenceScore"].max()), 2) if not predictions.empty and "ConfidenceScore" in predictions.columns else 0

    rows = [
        {
            "ExecutiveMetric": "Historical Draw Records",
            "MetricValue": int(len(history)),
            "Interpretation": "Lottery history available in the SQLite warehouse.",
            "UpdatedAt": _now(),
        },
        {
            "ExecutiveMetric": "Current Prediction Records",
            "MetricValue": int(len(predictions)),
            "Interpretation": "Lottery prediction rows currently available to the platform.",
            "UpdatedAt": _now(),
        },
        {
            "ExecutiveMetric": "Active Prediction Games",
            "MetricValue": int(predictions["GameName"].nunique()) if not predictions.empty and "GameName" in predictions.columns else 0,
            "Interpretation": "Unique lottery games represented in the current prediction set.",
            "UpdatedAt": _now(),
        },
        {
            "ExecutiveMetric": "Average Confidence",
            "MetricValue": avg_conf,
            "Interpretation": "Average confidence score across current lottery signals.",
            "UpdatedAt": _now(),
        },
        {
            "ExecutiveMetric": "Best Confidence",
            "MetricValue": best_conf,
            "Interpretation": "Highest current confidence signal in the platform.",
            "UpdatedAt": _now(),
        },
        {
            "ExecutiveMetric": "Model Leaderboard Rows",
            "MetricValue": int(len(leaderboard)),
            "Interpretation": "Rows available in the SQLite model leaderboard table.",
            "UpdatedAt": _now(),
        },
    ]

    return pd.DataFrame(rows)


def build_coverage_summary(master_df: pd.DataFrame | None = None) -> pd.DataFrame:
    history = load_master_data() if master_df is None else master_df.copy()
    predictions = load_base_predictions()

    if history.empty and predictions.empty:
        return pd.DataFrame()

    history_summary = pd.DataFrame()
    if not history.empty and "GameName" in history.columns:
        history_summary = (
            history.groupby(["GameFamily", "GameName"], dropna=False)
            .agg(
                HistoricalDraws=("GameName", "size"),
                LatestDrawDate=("DrawDate", "max") if "DrawDate" in history.columns else ("GameName", "size"),
            )
            .reset_index()
        )

    prediction_summary = pd.DataFrame()
    if not predictions.empty and "GameName" in predictions.columns:
        prediction_summary = (
            predictions.groupby(["GameFamily", "GameName"], dropna=False)
            .agg(
                CurrentPredictions=("GameName", "size"),
                AverageConfidence=("ConfidenceScore", "mean"),
                BestConfidence=("ConfidenceScore", "max"),
            )
            .reset_index()
        )
        prediction_summary["AverageConfidence"] = prediction_summary["AverageConfidence"].round(2)
        prediction_summary["BestConfidence"] = prediction_summary["BestConfidence"].round(2)

    if not history_summary.empty and not prediction_summary.empty:
        out = history_summary.merge(prediction_summary, on=["GameFamily", "GameName"], how="outer")
    elif not history_summary.empty:
        out = history_summary
        out["CurrentPredictions"] = 0
        out["AverageConfidence"] = 0
        out["BestConfidence"] = 0
    else:
        out = prediction_summary
        out["HistoricalDraws"] = 0
        out["LatestDrawDate"] = ""

    if "LatestDrawDate" in out.columns:
        out["LatestDrawDate"] = pd.to_datetime(out["LatestDrawDate"], errors="coerce").dt.strftime("%Y-%m-%d")

    out["UpdatedAt"] = _now()
    return out.sort_values(["GameFamily", "GameName"]).reset_index(drop=True)


def build_platform_status() -> pd.DataFrame:
    status = _safe_df("platform_refresh_status")
    logs = _safe_df("platform_run_log")

    rows: list[dict] = []

    if not status.empty:
        latest = status.tail(1).iloc[0]
        rows.append(
            {
                "StatusArea": "Latest Pipeline Status",
                "StatusValue": latest.get("Status", "Unknown"),
                "Detail": f"Run {latest.get('RunID', '')} completed at {latest.get('FinishedAt', '')}.",
                "UpdatedAt": _now(),
            }
        )
    else:
        rows.append(
            {
                "StatusArea": "Latest Pipeline Status",
                "StatusValue": "Unknown",
                "Detail": "platform_refresh_status table not found yet.",
                "UpdatedAt": _now(),
            }
        )

    if not logs.empty:
        rows.append(
            {
                "StatusArea": "Pipeline Log Rows",
                "StatusValue": int(len(logs)),
                "Detail": "Rows recorded in platform_run_log.",
                "UpdatedAt": _now(),
            }
        )

        failed = int((logs.get("Status", pd.Series(dtype=str)).astype(str).str.lower() == "failed").sum()) if "Status" in logs.columns else 0
        rows.append(
            {
                "StatusArea": "Pipeline Failures",
                "StatusValue": failed,
                "Detail": "Failed step rows recorded in platform_run_log.",
                "UpdatedAt": _now(),
            }
        )

    db_summary = get_database_summary()
    if not db_summary.empty:
        rows.append(
            {
                "StatusArea": "SQLite Tables",
                "StatusValue": int(len(db_summary)),
                "Detail": "Total tables visible in the SQLite warehouse.",
                "UpdatedAt": _now(),
            }
        )

    return pd.DataFrame(rows)


def build_statistical_insights(
    master_df: pd.DataFrame | None = None,
    predictions_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    history = load_master_data() if master_df is None else master_df.copy()
    predictions = load_base_predictions() if predictions_df is None else predictions_df.copy()

    rows: list[dict] = []

    if not predictions.empty and "ConfidenceScore" in predictions.columns:
        rows.extend(
            [
                {
                    "InsightArea": "Confidence Distribution",
                    "InsightValue": int((predictions["ConfidenceScore"] >= 90).sum()),
                    "Insight": "Current elite prediction count, using confidence >= 90.",
                    "UpdatedAt": _now(),
                },
                {
                    "InsightArea": "Confidence Distribution",
                    "InsightValue": int((predictions["ConfidenceScore"] >= 80).sum()),
                    "Insight": "Current high-or-better prediction count, using confidence >= 80.",
                    "UpdatedAt": _now(),
                },
            ]
        )

    if not history.empty and "DrawDate" in history.columns and history["DrawDate"].notna().any():
        rows.append(
            {
                "InsightArea": "History Currency",
                "InsightValue": history["DrawDate"].max().strftime("%Y-%m-%d"),
                "Insight": "Most recent historical lottery draw stored in SQLite.",
                "UpdatedAt": _now(),
            }
        )

    rows.append(
        {
            "InsightArea": "Architecture",
            "InsightValue": "SQLite-first",
            "Insight": "Executive report generated from SQLite runtime tables only; Excel is no longer required at runtime.",
            "UpdatedAt": _now(),
        }
    )

    return pd.DataFrame(rows)


def build_latest_results(master_df: pd.DataFrame | None = None) -> pd.DataFrame:
    return build_daily_latest_results(master_df)


# =========================================================
# EXPORT
# =========================================================


def export_executive_report() -> dict[str, int]:
    print("\n======================================")
    print("SQLITE EXECUTIVE LOTTERY REPORT")
    print("======================================")

    history = load_master_data()
    predictions = load_base_predictions()
    leaderboard = load_unified_leaderboard()

    outputs = {
        EXECUTIVE_SUMMARY_TABLE: build_executive_summary(history, predictions, leaderboard),
        EXECUTIVE_LATEST_RESULTS_TABLE: build_latest_results(history),
        EXECUTIVE_COVERAGE_TABLE: build_coverage_summary(history),
        EXECUTIVE_PLATFORM_STATUS_TABLE: build_platform_status(),
        EXECUTIVE_STATISTICS_TABLE: build_statistical_insights(history, predictions),
        EXECUTIVE_TOP_SIGNALS_TABLE: build_top_predictions(predictions, top_n=15),
    }

    row_counts: dict[str, int] = {}
    for table_name, df in outputs.items():
        row_counts[table_name] = replace_sqlite_table(table_name, df)

    create_indexes(EXECUTIVE_LATEST_RESULTS_TABLE, ["GameFamily", "GameName", "DrawDate"])
    create_indexes(EXECUTIVE_COVERAGE_TABLE, ["GameFamily", "GameName"])
    create_indexes(EXECUTIVE_TOP_SIGNALS_TABLE, ["GameFamily", "GameName", "ConfidenceScore"])

    print("\nSQLite executive report tables refreshed.")
    for table_name, rows in row_counts.items():
        print(f"{table_name}: {rows}")
    print("======================================\n")

    return row_counts


def main() -> dict[str, int]:
    return export_executive_report()


if __name__ == "__main__":
    main()
