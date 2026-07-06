from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.data.database import table_exists
from src.data.sqlite_store import create_indexes, read_sqlite_table, replace_sqlite_table
from src.lottery.scoring.unified_model_performance_dashboard import (
    _confidence_label,
    _format_number_set,
    load_predictions,
)


# =========================================================
# SQLITE-FIRST POWERBALL MODEL PERFORMANCE DASHBOARD
# =========================================================

POWERBALL_DASHBOARD_TABLE = "lottery_powerball_model_dashboard_summary"
POWERBALL_LEADERBOARD_TABLE = "lottery_powerball_model_leaderboard"
POWERBALL_RANDOM_TABLE = "lottery_powerball_model_vs_random"
POWERBALL_NOTES_TABLE = "lottery_powerball_model_notes"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_powerball_predictions() -> pd.DataFrame:
    df = load_predictions()
    if df.empty:
        return df

    if "GameFamily" in df.columns:
        filtered = df[df["GameFamily"].astype(str).str.contains("Power", case=False, na=False)].copy()
        if not filtered.empty:
            return filtered

    if "GameName" in df.columns:
        return df[df["GameName"].astype(str).str.contains("Power", case=False, na=False)].copy()

    return pd.DataFrame()


# Backward compatible loader name.
def load_powerball_comparison() -> pd.DataFrame:
    return load_powerball_predictions()


def build_dashboard_summary(summary_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_powerball_predictions() if summary_df is None else summary_df.copy()

    if df.empty:
        return pd.DataFrame(
            [
                {
                    "Metric": "PowerBall Runtime Predictions",
                    "Value": 0,
                    "Description": "No PowerBall rows found in lottery_predictions.",
                    "UpdatedAt": _now(),
                }
            ]
        )

    avg_conf = round(float(df["ConfidenceScore"].mean()), 2)
    best_conf = round(float(df["ConfidenceScore"].max()), 2)

    latest_generated = ""
    if "GeneratedAt" in df.columns and df["GeneratedAt"].notna().any():
        latest_generated = pd.to_datetime(df["GeneratedAt"], errors="coerce").max().strftime("%Y-%m-%d %H:%M:%S")

    rows = [
        {
            "Metric": "PowerBall Runtime Predictions",
            "Value": int(len(df)),
            "Description": "PowerBall and PowerBall Plus predictions currently available in SQLite.",
            "UpdatedAt": _now(),
        },
        {
            "Metric": "Average Confidence",
            "Value": avg_conf,
            "Description": "Average confidence score for PowerBall-family predictions.",
            "UpdatedAt": _now(),
        },
        {
            "Metric": "Best Confidence",
            "Value": best_conf,
            "Description": "Highest confidence score in current PowerBall-family predictions.",
            "UpdatedAt": _now(),
        },
        {
            "Metric": "Elite Predictions",
            "Value": int((df["ConfidenceScore"] >= 90).sum()),
            "Description": "PowerBall-family predictions scoring 90 or higher.",
            "UpdatedAt": _now(),
        },
        {
            "Metric": "Latest Prediction Run",
            "Value": latest_generated,
            "Description": "Latest GeneratedAt timestamp for PowerBall-family predictions.",
            "UpdatedAt": _now(),
        },
    ]

    return pd.DataFrame(rows)


def build_leaderboard(summary_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_powerball_predictions() if summary_df is None else summary_df.copy()
    if df.empty:
        return pd.DataFrame()

    keep_cols = [
        "GameFamily",
        "GameName",
        "PredictionRank",
        "NumberSetDisplay",
        "ConfidenceScore",
        "ConfidenceLabel",
        "ModelName",
        "ModelVersion",
        "RuleVersion",
        "RegularRange",
        "BonusRange",
        "GeneratedAt",
    ]

    for column in keep_cols:
        if column not in df.columns:
            if column == "NumberSetDisplay":
                df[column] = df.apply(_format_number_set, axis=1)
            elif column == "ConfidenceLabel":
                df[column] = df["ConfidenceScore"].apply(_confidence_label)
            else:
                df[column] = ""

    out = df.sort_values("ConfidenceScore", ascending=False)[keep_cols].copy()
    out["UpdatedAt"] = _now()
    return out.reset_index(drop=True)


def build_random_comparison(summary_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_powerball_predictions() if summary_df is None else summary_df.copy()
    if df.empty:
        return pd.DataFrame()

    rows = []
    for game_name, group in df.groupby("GameName", dropna=False):
        rows.append(
            {
                "GameName": game_name,
                "PredictionCount": int(len(group)),
                "AverageConfidence": round(float(group["ConfidenceScore"].mean()), 2),
                "BestConfidence": round(float(group["ConfidenceScore"].max()), 2),
                "BaselineDescription": "Model confidence is a ranking signal. It is not a jackpot probability and should not be read as guaranteed accuracy.",
                "UpdatedAt": _now(),
            }
        )

    return pd.DataFrame(rows)


def build_hit_pivot(hit_distribution_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_powerball_predictions() if hit_distribution_df is None else hit_distribution_df.copy()
    if df.empty:
        return pd.DataFrame()

    if "ConfidenceLabel" not in df.columns:
        df["ConfidenceLabel"] = df["ConfidenceScore"].apply(_confidence_label)

    out = (
        df.groupby(["GameName", "ConfidenceLabel"], dropna=False)
        .size()
        .reset_index(name="PredictionCount")
    )
    out["UpdatedAt"] = _now()
    return out


def build_rank_effectiveness(rank_summary_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_powerball_predictions() if rank_summary_df is None else rank_summary_df.copy()
    if df.empty:
        return pd.DataFrame()

    if "PredictionRank" not in df.columns:
        df["PredictionRank"] = range(1, len(df) + 1)

    out = (
        df.groupby(["GameName", "PredictionRank"], dropna=False)
        .agg(
            AvgConfidence=("ConfidenceScore", "mean"),
            PredictionCount=("GameName", "size"),
        )
        .reset_index()
    )
    out["AvgConfidence"] = out["AvgConfidence"].round(2)
    out["UpdatedAt"] = _now()
    return out


def build_model_notes() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "NoteType": "Runtime Source",
                "Note": "PowerBall model dashboard now reads from SQLite lottery_predictions only.",
                "UpdatedAt": _now(),
            },
            {
                "NoteType": "Interpretation",
                "Note": "Scores rank candidate sets. They do not guarantee draw outcomes.",
                "UpdatedAt": _now(),
            },
        ]
    )


def export_model_performance_dashboard() -> dict[str, int]:
    print("\n======================================")
    print("SQLITE POWERBALL MODEL PERFORMANCE")
    print("======================================")

    df = load_powerball_predictions()
    dashboard = build_dashboard_summary(df)
    leaderboard = build_leaderboard(df)
    random_comparison = build_random_comparison(df)
    notes = build_model_notes()

    outputs = {
        POWERBALL_DASHBOARD_TABLE: dashboard,
        POWERBALL_LEADERBOARD_TABLE: leaderboard,
        POWERBALL_RANDOM_TABLE: random_comparison,
        POWERBALL_NOTES_TABLE: notes,
    }

    row_counts: dict[str, int] = {}
    for table_name, out_df in outputs.items():
        row_counts[table_name] = replace_sqlite_table(table_name, out_df)

    create_indexes(POWERBALL_LEADERBOARD_TABLE, ["GameName", "ConfidenceScore", "PredictionRank"])

    print("\nSQLite PowerBall scoring tables refreshed.")
    for table_name, rows in row_counts.items():
        print(f"{table_name}: {rows}")
    print("======================================\n")

    return row_counts


# Compatibility placeholders retained for old imports.
def style_header(ws):
    return ws


def auto_fit_columns(ws):
    return ws


def style_body(ws):
    return ws


def add_conditional_formatting(ws):
    return ws


def style_dashboard_workbook():
    return None


def main() -> dict[str, int]:
    return export_model_performance_dashboard()


if __name__ == "__main__":
    main()
