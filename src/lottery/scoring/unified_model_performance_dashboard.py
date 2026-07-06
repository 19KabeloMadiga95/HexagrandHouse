from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.data.database import get_database_summary, table_exists
from src.data.sqlite_store import create_indexes, read_sqlite_table, replace_sqlite_table


# =========================================================
# SQLITE-FIRST LOTTERY MODEL PERFORMANCE DASHBOARD
# =========================================================

PREDICTIONS_TABLE = "lottery_predictions"
HISTORY_TABLE = "lottery_history"

DASHBOARD_TABLE = "lottery_model_dashboard_summary"
LEADERBOARD_TABLE = "lottery_model_leaderboard"
BEST_BY_GAME_TABLE = "lottery_model_best_by_game"
VS_RANDOM_TABLE = "lottery_model_vs_random"
GAME_SUMMARY_TABLE = "lottery_model_game_summary"
NOTES_TABLE = "lottery_model_notes"

NUMBER_COLUMNS = ["N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_df(table_name: str) -> pd.DataFrame:
    if not table_exists(table_name):
        return pd.DataFrame()
    return read_sqlite_table(table_name)


def _to_datetime(df: pd.DataFrame, column: str) -> pd.DataFrame:
    out = df.copy()
    if column in out.columns:
        out[column] = pd.to_datetime(out[column], errors="coerce")
    return out


def _safe_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def _confidence_label(score: Any) -> str:
    try:
        value = float(score)
    except Exception:
        return "Unrated"

    if value >= 90:
        return "Elite"
    if value >= 80:
        return "High"
    if value >= 65:
        return "Medium"
    return "Low"


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


def _parse_range_max(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if "-" in text:
        text = text.split("-")[-1]
    try:
        return int(float(text))
    except Exception:
        return None


# =========================================================
# LOADERS
# =========================================================


def load_predictions() -> pd.DataFrame:
    df = _safe_df(PREDICTIONS_TABLE)

    if df.empty:
        return df

    df = _to_datetime(df, "GeneratedAt")
    df = _safe_numeric(df, NUMBER_COLUMNS + ["ConfidenceScore", "EnsembleConfidenceScore", "PredictionRank", "RawScore", "RegularPickCount"])

    if "EnsembleConfidenceScore" in df.columns:
        df["ConfidenceScore"] = df["EnsembleConfidenceScore"].combine_first(df.get("ConfidenceScore"))

    if "ConfidenceScore" not in df.columns:
        df["ConfidenceScore"] = 0

    df["ConfidenceScore"] = pd.to_numeric(df["ConfidenceScore"], errors="coerce").fillna(0)

    if "ConfidenceLabel" not in df.columns:
        df["ConfidenceLabel"] = df["ConfidenceScore"].apply(_confidence_label)

    if "NumberSetDisplay" not in df.columns:
        df["NumberSetDisplay"] = df.apply(_format_number_set, axis=1)

    return df


def load_history() -> pd.DataFrame:
    df = _safe_df(HISTORY_TABLE)
    if df.empty:
        return df

    df = _to_datetime(df, "DrawDate")
    return df


# =========================================================
# BUILDERS
# =========================================================


def build_dashboard_summary(combined_df: pd.DataFrame | None = None, missing_df: pd.DataFrame | None = None) -> pd.DataFrame:
    predictions = load_predictions() if combined_df is None else combined_df.copy()
    history = load_history()

    if predictions.empty:
        return pd.DataFrame(
            [
                {
                    "Metric": "Runtime Predictions",
                    "Value": 0,
                    "Description": "No rows found in lottery_predictions.",
                    "UpdatedAt": _now(),
                }
            ]
        )

    latest_generated = ""
    if "GeneratedAt" in predictions.columns and predictions["GeneratedAt"].notna().any():
        latest_generated = predictions["GeneratedAt"].max().strftime("%Y-%m-%d %H:%M:%S")

    avg_conf = round(float(predictions["ConfidenceScore"].mean()), 2)
    elite_count = int((predictions["ConfidenceScore"] >= 90).sum())
    high_plus_count = int((predictions["ConfidenceScore"] >= 80).sum())

    rows = [
        {
            "Metric": "Runtime Predictions",
            "Value": int(len(predictions)),
            "Description": "Rows currently available to the Streamlit runtime.",
            "UpdatedAt": _now(),
        },
        {
            "Metric": "Active Games",
            "Value": int(predictions["GameName"].nunique()) if "GameName" in predictions.columns else 0,
            "Description": "Unique lottery games represented in current predictions.",
            "UpdatedAt": _now(),
        },
        {
            "Metric": "Average Confidence",
            "Value": avg_conf,
            "Description": "Average model/ensemble confidence score across current predictions.",
            "UpdatedAt": _now(),
        },
        {
            "Metric": "Elite Predictions",
            "Value": elite_count,
            "Description": "Predictions with confidence score of 90 or higher.",
            "UpdatedAt": _now(),
        },
        {
            "Metric": "High+ Predictions",
            "Value": high_plus_count,
            "Description": "Predictions with confidence score of 80 or higher.",
            "UpdatedAt": _now(),
        },
        {
            "Metric": "Latest Prediction Run",
            "Value": latest_generated,
            "Description": "Latest GeneratedAt timestamp from lottery_predictions.",
            "UpdatedAt": _now(),
        },
        {
            "Metric": "Historical Draws",
            "Value": int(len(history)),
            "Description": "Rows currently stored in lottery_history.",
            "UpdatedAt": _now(),
        },
    ]

    return pd.DataFrame(rows)


def build_unified_leaderboard(combined_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_predictions() if combined_df is None else combined_df.copy()

    if df.empty:
        return pd.DataFrame()

    for col in ["GameFamily", "GameName", "ModelName", "ModelVersion"]:
        if col not in df.columns:
            df[col] = "Unknown"

    grouped = (
        df.groupby(["GameFamily", "GameName", "ModelName", "ModelVersion"], dropna=False)
        .agg(
            PredictionCount=("GameName", "size"),
            AvgConfidence=("ConfidenceScore", "mean"),
            BestConfidence=("ConfidenceScore", "max"),
            EliteCount=("ConfidenceScore", lambda s: int((s >= 90).sum())),
            HighPlusCount=("ConfidenceScore", lambda s: int((s >= 80).sum())),
            BestRank=("PredictionRank", "min") if "PredictionRank" in df.columns else ("ConfidenceScore", "size"),
            LatestGeneratedAt=("GeneratedAt", "max") if "GeneratedAt" in df.columns else ("ConfidenceScore", "size"),
        )
        .reset_index()
    )

    grouped["AvgConfidence"] = grouped["AvgConfidence"].round(2)
    grouped["BestConfidence"] = grouped["BestConfidence"].round(2)
    grouped["PerformanceBand"] = grouped["AvgConfidence"].apply(_confidence_label)
    grouped["UpdatedAt"] = _now()

    if "LatestGeneratedAt" in grouped.columns:
        grouped["LatestGeneratedAt"] = pd.to_datetime(grouped["LatestGeneratedAt"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")

    return grouped.sort_values(["AvgConfidence", "BestConfidence"], ascending=False).reset_index(drop=True)


def build_best_by_game(combined_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_predictions() if combined_df is None else combined_df.copy()

    if df.empty:
        return pd.DataFrame()

    sort_cols = ["GameName", "ConfidenceScore"]
    df = df.sort_values(sort_cols, ascending=[True, False]).copy()
    best = df.groupby("GameName", dropna=False).head(1).copy()

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
        "RuleVersion",
        "GeneratedAt",
    ]

    for column in keep_cols:
        if column not in best.columns:
            best[column] = ""

    best["UpdatedAt"] = _now()
    return best[keep_cols + ["UpdatedAt"]].reset_index(drop=True)


def build_vs_random(combined_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_predictions() if combined_df is None else combined_df.copy()

    if df.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for game_name, group in df.groupby("GameName", dropna=False):
        sample = group.iloc[0]
        regular_max = _parse_range_max(sample.get("RegularRange"))
        pick_count = sample.get("RegularPickCount")
        try:
            pick_count = int(float(pick_count))
        except Exception:
            pick_count = None

        baseline_note = "Range metadata unavailable."
        approx_single_number_hit_rate = None
        if regular_max and pick_count:
            approx_single_number_hit_rate = round((pick_count / regular_max) * 100, 4)
            baseline_note = (
                "Approximate chance that one randomly selected regular number appears "
                "in a draw; this is a baseline indicator, not a jackpot probability."
            )

        rows.append(
            {
                "GameName": game_name,
                "PredictionCount": int(len(group)),
                "AverageModelConfidence": round(float(group["ConfidenceScore"].mean()), 2),
                "BestModelConfidence": round(float(group["ConfidenceScore"].max()), 2),
                "RegularRange": sample.get("RegularRange", ""),
                "RegularPickCount": pick_count,
                "ApproxRandomSingleNumberHitRatePct": approx_single_number_hit_rate,
                "BaselineNote": baseline_note,
                "UpdatedAt": _now(),
            }
        )

    return pd.DataFrame(rows).sort_values("AverageModelConfidence", ascending=False).reset_index(drop=True)


def build_game_summary(combined_df: pd.DataFrame | None = None) -> pd.DataFrame:
    predictions = load_predictions() if combined_df is None else combined_df.copy()
    history = load_history()

    if predictions.empty:
        return pd.DataFrame()

    pred_summary = (
        predictions.groupby(["GameFamily", "GameName"], dropna=False)
        .agg(
            PredictionCount=("GameName", "size"),
            AvgConfidence=("ConfidenceScore", "mean"),
            BestConfidence=("ConfidenceScore", "max"),
            EliteCount=("ConfidenceScore", lambda s: int((s >= 90).sum())),
        )
        .reset_index()
    )

    pred_summary["AvgConfidence"] = pred_summary["AvgConfidence"].round(2)
    pred_summary["BestConfidence"] = pred_summary["BestConfidence"].round(2)

    if not history.empty and "GameName" in history.columns:
        hist_summary = (
            history.groupby("GameName", dropna=False)
            .agg(
                HistoricalDraws=("GameName", "size"),
                LatestDrawDate=("DrawDate", "max") if "DrawDate" in history.columns else ("GameName", "size"),
            )
            .reset_index()
        )
        if "LatestDrawDate" in hist_summary.columns:
            hist_summary["LatestDrawDate"] = pd.to_datetime(hist_summary["LatestDrawDate"], errors="coerce").dt.strftime("%Y-%m-%d")

        pred_summary = pred_summary.merge(hist_summary, on="GameName", how="left")
    else:
        pred_summary["HistoricalDraws"] = 0
        pred_summary["LatestDrawDate"] = ""

    pred_summary["UpdatedAt"] = _now()
    return pred_summary.sort_values(["GameFamily", "GameName"]).reset_index(drop=True)


def build_notes() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "NoteType": "Architecture",
                "Note": "This dashboard is generated from SQLite runtime tables only. No Excel workbook is required at runtime.",
                "UpdatedAt": _now(),
            },
            {
                "NoteType": "Responsible Use",
                "Note": "Confidence scores are model-ranking signals, not guarantees of lottery outcomes.",
                "UpdatedAt": _now(),
            },
            {
                "NoteType": "Source Tables",
                "Note": "Primary source tables: lottery_predictions and lottery_history.",
                "UpdatedAt": _now(),
            },
        ]
    )


# Backward compatible alias used by older scripts.
def load_all_summaries() -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_predictions(), pd.DataFrame()


# =========================================================
# EXPORT
# =========================================================


def export_unified_model_performance_dashboard() -> dict[str, int]:
    print("\n======================================")
    print("SQLITE LOTTERY MODEL PERFORMANCE")
    print("======================================")

    predictions = load_predictions()

    dashboard = build_dashboard_summary(predictions)
    leaderboard = build_unified_leaderboard(predictions)
    best_by_game = build_best_by_game(predictions)
    vs_random = build_vs_random(predictions)
    game_summary = build_game_summary(predictions)
    notes = build_notes()

    outputs = {
        DASHBOARD_TABLE: dashboard,
        LEADERBOARD_TABLE: leaderboard,
        BEST_BY_GAME_TABLE: best_by_game,
        VS_RANDOM_TABLE: vs_random,
        GAME_SUMMARY_TABLE: game_summary,
        NOTES_TABLE: notes,
    }

    row_counts: dict[str, int] = {}
    for table_name, df in outputs.items():
        rows = replace_sqlite_table(table_name, df)
        row_counts[table_name] = rows

    create_indexes(LEADERBOARD_TABLE, ["GameFamily", "GameName", "AvgConfidence"])
    create_indexes(BEST_BY_GAME_TABLE, ["GameFamily", "GameName", "ConfidenceScore"])
    create_indexes(GAME_SUMMARY_TABLE, ["GameFamily", "GameName"])

    print("\nSQLite scoring tables refreshed.")
    for table_name, rows in row_counts.items():
        print(f"{table_name}: {rows}")
    print("======================================\n")

    return row_counts


def style_header(ws):
    """Compatibility placeholder. Styling is no longer needed because output is SQLite."""
    return ws


def auto_fit_columns(ws):
    """Compatibility placeholder. Styling is no longer needed because output is SQLite."""
    return ws


def style_body(ws):
    """Compatibility placeholder. Styling is no longer needed because output is SQLite."""
    return ws


def add_conditional_formatting(ws):
    """Compatibility placeholder. Styling is no longer needed because output is SQLite."""
    return ws


def style_workbook():
    """Compatibility placeholder. Styling is no longer needed because output is SQLite."""
    return None


def main() -> dict[str, int]:
    return export_unified_model_performance_dashboard()


if __name__ == "__main__":
    main()
