from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.data.database import get_database_summary, table_exists
from src.data.sqlite_store import create_indexes, read_sqlite_table, replace_sqlite_table


# =========================================================
# SQLITE-FIRST DAILY LOTTERY SUMMARY GENERATOR
# =========================================================

PREDICTIONS_TABLE = "lottery_predictions"
HISTORY_TABLE = "lottery_history"
LEADERBOARD_TABLE = "lottery_model_leaderboard"
QUALITY_TABLE = "lottery_daily_quality_snapshot"

TODAY_SNAPSHOT_TABLE = "lottery_daily_summary_snapshot"
LATEST_RESULTS_TABLE = "lottery_daily_latest_results"
TOP_PREDICTIONS_TABLE = "lottery_daily_top_predictions"
BEST_MODEL_TABLE = "lottery_daily_best_models"
QUICK_INSIGHTS_TABLE = "lottery_daily_quick_insights"

NUMBER_COLUMNS = ["N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_df(table_name: str) -> pd.DataFrame:
    if not table_exists(table_name):
        return pd.DataFrame()
    return read_sqlite_table(table_name)


def _safe_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    out = df.copy()
    out = out.dropna(how="all")
    return out.reset_index(drop=True)


def dataframe_to_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def _format_number_set(row: pd.Series) -> str:
    numbers: list[str] = []
    for column in ["N1", "N2", "N3", "N4", "N5", "N6"]:
        value = row.get(column)
        if pd.notna(value):
            try:
                numbers.append(str(int(float(value))))
            except Exception:
                numbers.append(str(value))

    bonus = row.get("Bonus")
    if pd.notna(bonus):
        try:
            return f"{'-'.join(numbers)} | Bonus {int(float(bonus))}"
        except Exception:
            return f"{'-'.join(numbers)} | Bonus {bonus}"

    return "-".join(numbers)


# =========================================================
# LOADERS - BACKWARD COMPATIBLE NAMES
# =========================================================


def load_master_data() -> pd.DataFrame:
    df = _safe_df(HISTORY_TABLE)
    if df.empty:
        return df
    if "DrawDate" in df.columns:
        df["DrawDate"] = pd.to_datetime(df["DrawDate"], errors="coerce")
    return _safe_numeric(df, NUMBER_COLUMNS)


def load_quality_summary() -> pd.DataFrame:
    return _safe_df(QUALITY_TABLE)


def load_unified_leaderboard() -> pd.DataFrame:
    return _safe_df(LEADERBOARD_TABLE)


def load_best_by_game() -> pd.DataFrame:
    return _safe_df("lottery_model_best_by_game")


def load_vs_random() -> pd.DataFrame:
    return _safe_df("lottery_model_vs_random")


def load_final_ensembles() -> pd.DataFrame:
    return load_base_predictions()


def load_base_predictions() -> pd.DataFrame:
    df = _safe_df(PREDICTIONS_TABLE)
    if df.empty:
        return df

    if "GeneratedAt" in df.columns:
        df["GeneratedAt"] = pd.to_datetime(df["GeneratedAt"], errors="coerce")

    df = _safe_numeric(df, NUMBER_COLUMNS + ["ConfidenceScore", "EnsembleConfidenceScore", "PredictionRank"])

    if "EnsembleConfidenceScore" in df.columns:
        df["ConfidenceScore"] = df["EnsembleConfidenceScore"].combine_first(df.get("ConfidenceScore"))

    if "ConfidenceScore" not in df.columns:
        df["ConfidenceScore"] = 0

    df["ConfidenceScore"] = pd.to_numeric(df["ConfidenceScore"], errors="coerce").fillna(0)

    if "NumberSetDisplay" not in df.columns:
        df["NumberSetDisplay"] = df.apply(_format_number_set, axis=1)

    return df


# =========================================================
# BUILDERS
# =========================================================


def build_today_snapshot(
    master_df: pd.DataFrame | None = None,
    predictions_df: pd.DataFrame | None = None,
    quality_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    history = load_master_data() if master_df is None else master_df.copy()
    predictions = load_base_predictions() if predictions_df is None else predictions_df.copy()

    latest_generated = ""
    if not predictions.empty and "GeneratedAt" in predictions.columns and predictions["GeneratedAt"].notna().any():
        latest_generated = predictions["GeneratedAt"].max().strftime("%Y-%m-%d %H:%M:%S")

    latest_draw = ""
    if not history.empty and "DrawDate" in history.columns and history["DrawDate"].notna().any():
        latest_draw = history["DrawDate"].max().strftime("%Y-%m-%d")

    avg_conf = round(float(predictions["ConfidenceScore"].mean()), 2) if not predictions.empty and "ConfidenceScore" in predictions.columns else 0

    rows = [
        {
            "SnapshotMetric": "Historical Draws",
            "SnapshotValue": int(len(history)),
            "Description": "Rows available in lottery_history.",
            "UpdatedAt": _now(),
        },
        {
            "SnapshotMetric": "Current Predictions",
            "SnapshotValue": int(len(predictions)),
            "Description": "Rows available in lottery_predictions.",
            "UpdatedAt": _now(),
        },
        {
            "SnapshotMetric": "Latest Draw Date",
            "SnapshotValue": latest_draw,
            "Description": "Most recent DrawDate in lottery_history.",
            "UpdatedAt": _now(),
        },
        {
            "SnapshotMetric": "Latest Prediction Run",
            "SnapshotValue": latest_generated,
            "Description": "Most recent GeneratedAt in lottery_predictions.",
            "UpdatedAt": _now(),
        },
        {
            "SnapshotMetric": "Average Confidence",
            "SnapshotValue": avg_conf,
            "Description": "Average prediction confidence across current lottery predictions.",
            "UpdatedAt": _now(),
        },
    ]

    return pd.DataFrame(rows)


def build_latest_results(master_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_master_data() if master_df is None else master_df.copy()
    if df.empty:
        return pd.DataFrame()

    if "GameName" not in df.columns:
        df["GameName"] = "Unknown"
    if "DrawDate" not in df.columns:
        df["DrawDate"] = pd.NaT

    df = df.sort_values(["GameName", "DrawDate"], ascending=[True, False])
    latest = df.groupby("GameName", dropna=False).head(1).copy()

    latest["NumberSetDisplay"] = latest.apply(_format_number_set, axis=1)
    latest["UpdatedAt"] = _now()

    keep_cols = ["GameFamily", "GameName", "DrawType", "DrawDate", "NumberSetDisplay", "UpdatedAt"]
    for column in keep_cols:
        if column not in latest.columns:
            latest[column] = ""

    return latest[keep_cols].reset_index(drop=True)


def build_top_predictions(predictions_df: pd.DataFrame | None = None, top_n: int = 25) -> pd.DataFrame:
    df = load_base_predictions() if predictions_df is None else predictions_df.copy()
    if df.empty:
        return pd.DataFrame()

    df = df.sort_values("ConfidenceScore", ascending=False).head(top_n).copy()
    df["UpdatedAt"] = _now()

    keep_cols = [
        "GameFamily",
        "GameName",
        "DrawType",
        "PredictionRank",
        "NumberSetDisplay",
        "ConfidenceScore",
        "ConfidenceLabel",
        "ModelName",
        "ModelVersion",
        "GeneratedAt",
        "UpdatedAt",
    ]

    for column in keep_cols:
        if column not in df.columns:
            df[column] = ""

    return df[keep_cols].reset_index(drop=True)


def build_best_model_snapshot(leaderboard_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_unified_leaderboard() if leaderboard_df is None else leaderboard_df.copy()
    if df.empty:
        # Build directly from predictions if the scoring batch has not been run yet.
        predictions = load_base_predictions()
        if predictions.empty:
            return pd.DataFrame()
        df = (
            predictions.groupby(["GameFamily", "GameName"], dropna=False)
            .agg(
                PredictionCount=("GameName", "size"),
                AvgConfidence=("ConfidenceScore", "mean"),
                BestConfidence=("ConfidenceScore", "max"),
            )
            .reset_index()
        )
        df["ModelName"] = "SQLite Runtime"
        df["ModelVersion"] = "SQLiteRuntime_v1"

    if "AvgConfidence" in df.columns:
        df = df.sort_values("AvgConfidence", ascending=False)

    df["UpdatedAt"] = _now()
    return df.reset_index(drop=True)


def build_quick_insights(
    master_df: pd.DataFrame | None = None,
    predictions_df: pd.DataFrame | None = None,
    leaderboard_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    history = load_master_data() if master_df is None else master_df.copy()
    predictions = load_base_predictions() if predictions_df is None else predictions_df.copy()
    leaderboard = load_unified_leaderboard() if leaderboard_df is None else leaderboard_df.copy()

    insights: list[dict] = []

    insights.append(
        {
            "InsightType": "Runtime",
            "Insight": f"SQLite runtime currently holds {len(predictions)} lottery prediction rows.",
            "UpdatedAt": _now(),
        }
    )

    if not predictions.empty and "ConfidenceScore" in predictions.columns:
        best = predictions.sort_values("ConfidenceScore", ascending=False).iloc[0]
        insights.append(
            {
                "InsightType": "Top Signal",
                "Insight": f"Top current signal: {best.get('GameName', 'Unknown')} at {round(float(best.get('ConfidenceScore', 0)), 2)} confidence.",
                "UpdatedAt": _now(),
            }
        )

    if not history.empty and "DrawDate" in history.columns and history["DrawDate"].notna().any():
        latest_date = history["DrawDate"].max().strftime("%Y-%m-%d")
        insights.append(
            {
                "InsightType": "Latest Draw",
                "Insight": f"Latest stored historical lottery draw date is {latest_date}.",
                "UpdatedAt": _now(),
            }
        )

    if not leaderboard.empty and "GameName" in leaderboard.columns:
        insights.append(
            {
                "InsightType": "Coverage",
                "Insight": f"Model leaderboard covers {leaderboard['GameName'].nunique()} games.",
                "UpdatedAt": _now(),
            }
        )

    return pd.DataFrame(insights)


def build_quality_snapshot() -> pd.DataFrame:
    summary = get_database_summary()
    if summary.empty:
        return pd.DataFrame()

    summary = summary.copy()
    summary["Layer"] = summary["TableName"].apply(
        lambda name: "Lottery" if str(name).startswith("lottery_") else "Platform" if str(name).startswith("platform_") else "Other"
    )
    summary["Status"] = summary["RowCount"].apply(lambda rows: "Populated" if int(rows) > 0 else "Empty")
    summary["UpdatedAt"] = _now()
    return summary


# =========================================================
# EXPORT
# =========================================================


def export_daily_summary() -> dict[str, int]:
    print("\n======================================")
    print("SQLITE DAILY LOTTERY SUMMARY")
    print("======================================")

    history = load_master_data()
    predictions = load_base_predictions()
    leaderboard = load_unified_leaderboard()

    outputs = {
        TODAY_SNAPSHOT_TABLE: build_today_snapshot(history, predictions),
        LATEST_RESULTS_TABLE: build_latest_results(history),
        TOP_PREDICTIONS_TABLE: build_top_predictions(predictions),
        BEST_MODEL_TABLE: build_best_model_snapshot(leaderboard),
        QUICK_INSIGHTS_TABLE: build_quick_insights(history, predictions, leaderboard),
        QUALITY_TABLE: build_quality_snapshot(),
    }

    row_counts: dict[str, int] = {}
    for table_name, df in outputs.items():
        row_counts[table_name] = replace_sqlite_table(table_name, df)

    create_indexes(LATEST_RESULTS_TABLE, ["GameFamily", "GameName", "DrawDate"])
    create_indexes(TOP_PREDICTIONS_TABLE, ["GameFamily", "GameName", "ConfidenceScore"])
    create_indexes(BEST_MODEL_TABLE, ["GameFamily", "GameName"])

    print("\nSQLite daily summary tables refreshed.")
    for table_name, rows in row_counts.items():
        print(f"{table_name}: {rows}")
    print("======================================\n")

    return row_counts


def main() -> dict[str, int]:
    return export_daily_summary()


if __name__ == "__main__":
    main()
