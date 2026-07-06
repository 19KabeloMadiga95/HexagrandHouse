from __future__ import annotations

from datetime import datetime
from math import exp
from typing import Any

import pandas as pd

from src.data.sqlite_store import (
    create_indexes,
    read_sqlite_table,
    replace_sqlite_table,
)


# =========================================================
# SQLITE TABLES
# =========================================================

FEATURE_TABLE = "football_match_features"
GOALS_TABLE = "football_goals_model_predictions"
CORNERS_TABLE = "football_corners_model_predictions"
RESULT_TABLE = "football_result_model_predictions"
ENSEMBLE_TABLE = "football_ensemble_predictions"
RUNTIME_TABLE = "football_predictions"
SUMMARY_TABLE = "football_model_summary"


# =========================================================
# SHARED HELPERS
# =========================================================

def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def clamp_probability(value: Any, default: float = 0.5) -> float:
    value = safe_float(value, default)

    if value < 0:
        return 0.0

    if value > 1:
        return 1.0

    return float(value)


def sigmoid(value: float, centre: float = 0.0, scale: float = 1.0) -> float:
    try:
        z = (float(value) - centre) / max(float(scale), 0.0001)
        z = max(min(z, 12), -12)
        return 1 / (1 + exp(-z))
    except Exception:
        return 0.5


def confidence_label(probability: Any) -> str:
    probability = clamp_probability(probability, 0.0)

    if probability >= 0.85:
        return "Elite"

    if probability >= 0.75:
        return "Strong"

    if probability >= 0.65:
        return "Medium"

    if probability >= 0.55:
        return "Small"

    return "Weak"


def normalize_three_way(home: Any, draw: Any, away: Any) -> tuple[float, float, float]:
    home = max(safe_float(home, 0.333), 0.001)
    draw = max(safe_float(draw, 0.333), 0.001)
    away = max(safe_float(away, 0.333), 0.001)

    total = home + draw + away

    if total <= 0:
        return 0.333, 0.333, 0.333

    return (
        round(home / total, 4),
        round(draw / total, 4),
        round(away / total, 4),
    )


def add_match_key(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "MatchDate" in out.columns:
        match_date = pd.to_datetime(out["MatchDate"], errors="coerce")
        out["MatchDateKey"] = match_date.dt.strftime("%Y-%m-%d")
    else:
        out["MatchDateKey"] = ""

    for col in ["LeagueCode", "HomeTeam", "AwayTeam"]:
        if col not in out.columns:
            out[col] = ""

    out["MatchKey"] = (
        out["LeagueCode"].astype(str)
        + "_"
        + out["MatchDateKey"].astype(str)
        + "_"
        + out["HomeTeam"].astype(str)
        + "_"
        + out["AwayTeam"].astype(str)
    )

    return out


def select_existing_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return df[[col for col in columns if col in df.columns]].copy()


def load_match_features() -> pd.DataFrame:
    df = read_sqlite_table(FEATURE_TABLE)

    if df.empty:
        return pd.DataFrame()

    df = df.copy()

    if "MatchDate" in df.columns:
        df["MatchDate"] = pd.to_datetime(df["MatchDate"], errors="coerce")

    # Keep the model robust against older databases where some expected
    # engineered columns may not exist yet.
    expected_numeric = [
        "HomeGoals",
        "AwayGoals",
        "TotalGoals",
        "HomeCorners",
        "AwayCorners",
        "TotalCorners",
        "BTTS",
        "Over25Goals",
        "Over95Corners",
        "FormPointsDiff_Last3",
        "FormPointsDiff_Last5",
        "FormPointsDiff_Last10",
        "AttackStrengthDiff_Last3",
        "AttackStrengthDiff_Last5",
        "AttackStrengthDiff_Last10",
        "DefenceWeaknessDiff_Last3",
        "DefenceWeaknessDiff_Last5",
        "DefenceWeaknessDiff_Last10",
        "CornerAttackDiff_Last3",
        "CornerAttackDiff_Last5",
        "CornerAttackDiff_Last10",
        "Home_GoalsFor_Last3",
        "Home_GoalsFor_Last5",
        "Home_GoalsFor_Last10",
        "Away_GoalsFor_Last3",
        "Away_GoalsFor_Last5",
        "Away_GoalsFor_Last10",
        "Home_GoalsAgainst_Last3",
        "Home_GoalsAgainst_Last5",
        "Home_GoalsAgainst_Last10",
        "Away_GoalsAgainst_Last3",
        "Away_GoalsAgainst_Last5",
        "Away_GoalsAgainst_Last10",
        "Home_CornersFor_Last3",
        "Home_CornersFor_Last5",
        "Home_CornersFor_Last10",
        "Away_CornersFor_Last3",
        "Away_CornersFor_Last5",
        "Away_CornersFor_Last10",
        "Home_CornersAgainst_Last3",
        "Home_CornersAgainst_Last5",
        "Home_CornersAgainst_Last10",
        "Away_CornersAgainst_Last3",
        "Away_CornersAgainst_Last5",
        "Away_CornersAgainst_Last10",
        "Home_BTTS_Last5",
        "Away_BTTS_Last5",
        "Home_Over25Goals_Last5",
        "Away_Over25Goals_Last5",
        "Home_Over95Corners_Last5",
        "Away_Over95Corners_Last5",
    ]

    for col in expected_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "TotalGoals" not in df.columns:
        df["TotalGoals"] = df.get("HomeGoals", 0).fillna(0) + df.get("AwayGoals", 0).fillna(0)

    if "TotalCorners" not in df.columns:
        df["TotalCorners"] = df.get("HomeCorners", 0).fillna(0) + df.get("AwayCorners", 0).fillna(0)

    df = add_match_key(df)

    sort_cols = [col for col in ["MatchDate", "League", "HomeTeam", "AwayTeam"] if col in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, ascending=[False] + [True] * (len(sort_cols) - 1))

    return df.reset_index(drop=True)


def base_output_columns() -> list[str]:
    return [
        "MatchKey",
        "MatchDate",
        "Season",
        "SeasonCode",
        "LeagueCode",
        "League",
        "Country",
        "Tier",
        "HomeTeam",
        "AwayTeam",
        "HomeGoals",
        "AwayGoals",
        "TotalGoals",
        "HomeCorners",
        "AwayCorners",
        "TotalCorners",
        "Result",
        "ResultLabel",
        "BTTS",
        "Over25Goals",
        "Over95Corners",
    ]


def save_model_table(table_name: str, df: pd.DataFrame) -> int:
    rows = replace_sqlite_table(table_name, df)
    create_indexes(
        table_name,
        [
            "MatchKey",
            "MatchDate",
            "League",
            "LeagueCode",
            "HomeTeam",
            "AwayTeam",
            "GeneratedAt",
        ],
    )
    return rows


def write_summary(rows: list[dict[str, Any]]) -> int:
    summary = pd.DataFrame(rows)
    if not summary.empty:
        summary["UpdatedAt"] = now_string()
    return replace_sqlite_table(SUMMARY_TABLE, summary)
