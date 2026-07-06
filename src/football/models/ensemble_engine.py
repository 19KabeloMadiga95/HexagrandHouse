from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.data.sqlite_store import (
    create_indexes,
    read_sqlite_table,
    replace_sqlite_table,
)
from src.football.models.corners_model import export_corners_predictions
from src.football.models.goals_model import export_goals_predictions
from src.football.models.result_model import export_result_predictions
from src.football.models.sqlite_football_model_engine import (
    CORNERS_TABLE,
    ENSEMBLE_TABLE,
    GOALS_TABLE,
    RESULT_TABLE,
    RUNTIME_TABLE,
    SUMMARY_TABLE,
    clamp_probability,
    confidence_label,
    now_string,
    safe_float,
    write_summary,
)


# =========================================================
# ENSEMBLE CONFIG
# =========================================================

MODEL_NAME = "SQLite Football Ensemble"
MODEL_VERSION = "football_ensemble_sqlite_v1"


# =========================================================
# HELPERS
# =========================================================

def _ensure_model_tables() -> None:
    if read_sqlite_table(RESULT_TABLE, limit=1).empty:
        export_result_predictions()

    if read_sqlite_table(GOALS_TABLE, limit=1).empty:
        export_goals_predictions()

    if read_sqlite_table(CORNERS_TABLE, limit=1).empty:
        export_corners_predictions()


def _prepare_table(table_name: str, prefix: str, keep_columns: list[str]) -> pd.DataFrame:
    df = read_sqlite_table(table_name)

    if df.empty:
        return pd.DataFrame()

    df = df.copy()

    if "MatchKey" not in df.columns:
        return pd.DataFrame()

    columns = ["MatchKey"] + [col for col in keep_columns if col in df.columns]
    df = df[columns].copy()

    rename_map = {
        col: f"{prefix}{col}"
        for col in columns
        if col != "MatchKey"
    }

    return df.rename(columns=rename_map)


def _clean_base(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    if "MatchDate" in out.columns:
        out["MatchDate"] = pd.to_datetime(out["MatchDate"], errors="coerce")

    return out


def _actual_hit(row: pd.Series, market: str, signal: str, predicted_result: str | None) -> int | None:
    if market == "Result":
        actual = row.get("Result")
        if actual is None or pd.isna(actual):
            return None
        return int(str(actual) == str(predicted_result))

    if signal == "Over 1.5 Goals":
        total = safe_float(row.get("TotalGoals"), -1)
        return None if total < 0 else int(total > 1.5)

    if signal == "Over 2.5 Goals":
        total = safe_float(row.get("TotalGoals"), -1)
        return None if total < 0 else int(total > 2.5)

    if signal == "Over 3.5 Goals":
        total = safe_float(row.get("TotalGoals"), -1)
        return None if total < 0 else int(total > 3.5)

    if signal == "BTTS Yes":
        home = safe_float(row.get("HomeGoals"), -1)
        away = safe_float(row.get("AwayGoals"), -1)
        return None if home < 0 or away < 0 else int(home > 0 and away > 0)

    if signal == "Over 8.5 Corners":
        total = safe_float(row.get("TotalCorners"), -1)
        return None if total < 0 else int(total > 8.5)

    if signal == "Over 9.5 Corners":
        total = safe_float(row.get("TotalCorners"), -1)
        return None if total < 0 else int(total > 9.5)

    if signal == "Over 10.5 Corners":
        total = safe_float(row.get("TotalCorners"), -1)
        return None if total < 0 else int(total > 10.5)

    return None


def _pick_primary_signal(row: pd.Series) -> dict[str, Any]:
    candidates = [
        {
            "Market": "Result",
            "PrimaryMarketSignal": row.get("Result_PredictedResultLabel"),
            "PredictedResult": row.get("Result_PredictedResult"),
            "ModelProbability": row.get("Result_ModelProbability"),
            "SourceModel": "Result",
        },
        {
            "Market": "Goals",
            "PrimaryMarketSignal": row.get("Goals_PrimaryMarketSignal"),
            "PredictedResult": None,
            "ModelProbability": row.get("Goals_ModelProbability"),
            "SourceModel": "Goals",
        },
        {
            "Market": "Corners",
            "PrimaryMarketSignal": row.get("Corners_PrimaryMarketSignal"),
            "PredictedResult": None,
            "ModelProbability": row.get("Corners_ModelProbability"),
            "SourceModel": "Corners",
        },
    ]

    valid_candidates = []

    for candidate in candidates:
        probability = clamp_probability(candidate.get("ModelProbability"), 0.0)
        signal = candidate.get("PrimaryMarketSignal")

        if not signal or pd.isna(signal):
            continue

        candidate["ModelProbability"] = probability
        valid_candidates.append(candidate)

    if not valid_candidates:
        return {
            "Market": "Unknown",
            "PrimaryMarketSignal": "No Signal",
            "PredictedResult": None,
            "ModelProbability": 0.0,
            "SourceModel": "None",
        }

    return max(valid_candidates, key=lambda item: item["ModelProbability"])


def _make_summary(ensemble_df: pd.DataFrame) -> list[dict[str, Any]]:
    if ensemble_df.empty:
        return [
            {
                "Metric": "Rows",
                "Value": 0,
            }
        ]

    hit_rate = None
    if "PredictionHit" in ensemble_df.columns:
        hit_series = pd.to_numeric(ensemble_df["PredictionHit"], errors="coerce")
        if hit_series.notna().any():
            hit_rate = round(float(hit_series.mean()), 4)

    return [
        {
            "Metric": "Rows",
            "Value": int(len(ensemble_df)),
        },
        {
            "Metric": "Leagues",
            "Value": int(ensemble_df["League"].nunique()) if "League" in ensemble_df.columns else 0,
        },
        {
            "Metric": "AverageConfidence",
            "Value": round(float(pd.to_numeric(ensemble_df["EnsembleConfidenceScore"], errors="coerce").mean()), 4)
            if "EnsembleConfidenceScore" in ensemble_df.columns
            else 0,
        },
        {
            "Metric": "EliteSignals",
            "Value": int(pd.to_numeric(ensemble_df.get("ElitePrediction", 0), errors="coerce").fillna(0).sum()),
        },
        {
            "Metric": "HistoricalHitRate",
            "Value": hit_rate,
        },
    ]


# =========================================================
# ENSEMBLE BUILD
# =========================================================

def build_football_ensemble_predictions() -> pd.DataFrame:
    _ensure_model_tables()

    result_df = read_sqlite_table(RESULT_TABLE)

    if result_df.empty:
        return pd.DataFrame()

    base_columns = [
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

    base = result_df[[col for col in base_columns if col in result_df.columns]].copy()
    base = _clean_base(base)

    result_keep = [
        "PrimaryMarketSignal",
        "PredictedResult",
        "PredictedResultLabel",
        "HomeWinProbability",
        "DrawProbability",
        "AwayWinProbability",
        "PredictedResultProbability",
        "ModelProbability",
        "ConfidenceLabel",
    ]

    goals_keep = [
        "PrimaryMarketSignal",
        "GoalsSignal",
        "HomeExpectedGoals",
        "AwayExpectedGoals",
        "ExpectedTotalGoals",
        "Over15GoalsProbability",
        "Over25GoalsProbability",
        "Over35GoalsProbability",
        "BTTSProbability",
        "ModelProbability",
        "ConfidenceLabel",
    ]

    corners_keep = [
        "PrimaryMarketSignal",
        "CornersSignal",
        "HomeExpectedCorners",
        "AwayExpectedCorners",
        "ExpectedTotalCorners",
        "Over85CornersProbability",
        "Over95CornersProbability",
        "Over105CornersProbability",
        "ModelProbability",
        "ConfidenceLabel",
    ]

    result_model = _prepare_table(RESULT_TABLE, "Result_", result_keep)
    goals_model = _prepare_table(GOALS_TABLE, "Goals_", goals_keep)
    corners_model = _prepare_table(CORNERS_TABLE, "Corners_", corners_keep)

    ensemble = base.copy()

    for model_df in [result_model, goals_model, corners_model]:
        if not model_df.empty:
            ensemble = ensemble.merge(model_df, on="MatchKey", how="left")

    generated_at = now_string()
    rows: list[dict[str, Any]] = []

    for _, row in ensemble.iterrows():
        pick = _pick_primary_signal(row)
        probability = clamp_probability(pick.get("ModelProbability"), 0.0)
        label = confidence_label(probability)
        signal = str(pick.get("PrimaryMarketSignal", "No Signal"))
        market = str(pick.get("Market", "Unknown"))
        predicted_result = pick.get("PredictedResult")
        prediction_hit = _actual_hit(row, market, signal, predicted_result)

        output = row.to_dict()
        output.update(
            {
                "ModelName": MODEL_NAME,
                "ModelVersion": MODEL_VERSION,
                "SourceModel": pick.get("SourceModel"),
                "Market": market,
                "PrimaryMarketSignal": signal,
                "PredictedResult": predicted_result,
                "ModelProbability": probability,
                "ConfidenceScore": probability,
                "EnsembleConfidenceScore": probability,
                "ConfidenceLabel": label,
                "SignalLabel": label,
                "ElitePrediction": 1 if probability >= 0.85 else 0,
                "ValueScore": round(probability * 100, 2),
                "ValueRating": label,
                "PredictionHit": prediction_hit,
                "GeneratedAt": generated_at,
            }
        )
        rows.append(output)

    out = pd.DataFrame(rows)

    if "MatchDate" in out.columns:
        out["MatchDate"] = pd.to_datetime(out["MatchDate"], errors="coerce")
        out = out.sort_values(
            by=["MatchDate", "EnsembleConfidenceScore"],
            ascending=[False, False],
        )

    preferred_columns = [
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
        "ModelName",
        "ModelVersion",
        "SourceModel",
        "Market",
        "PrimaryMarketSignal",
        "PredictedResult",
        "ModelProbability",
        "ConfidenceScore",
        "EnsembleConfidenceScore",
        "ConfidenceLabel",
        "SignalLabel",
        "ElitePrediction",
        "ValueScore",
        "ValueRating",
        "PredictionHit",
        "GeneratedAt",
        "Result_PrimaryMarketSignal",
        "Result_PredictedResult",
        "Result_HomeWinProbability",
        "Result_DrawProbability",
        "Result_AwayWinProbability",
        "Goals_PrimaryMarketSignal",
        "Goals_ExpectedTotalGoals",
        "Goals_Over15GoalsProbability",
        "Goals_Over25GoalsProbability",
        "Goals_BTTSProbability",
        "Corners_PrimaryMarketSignal",
        "Corners_ExpectedTotalCorners",
        "Corners_Over85CornersProbability",
        "Corners_Over95CornersProbability",
    ]

    columns = [col for col in preferred_columns if col in out.columns]
    extra_columns = [col for col in out.columns if col not in columns]

    return out[columns + extra_columns].reset_index(drop=True)


def export_football_ensemble_predictions() -> pd.DataFrame:
    ensemble = build_football_ensemble_predictions()

    ensemble_rows = replace_sqlite_table(ENSEMBLE_TABLE, ensemble)
    runtime_rows = replace_sqlite_table(RUNTIME_TABLE, ensemble)

    for table in [ENSEMBLE_TABLE, RUNTIME_TABLE]:
        create_indexes(
            table,
            [
                "MatchKey",
                "MatchDate",
                "League",
                "LeagueCode",
                "HomeTeam",
                "AwayTeam",
                "Market",
                "ConfidenceLabel",
                "GeneratedAt",
            ],
        )

    write_summary(_make_summary(ensemble))

    print("\nSQLite football ensemble refreshed.")
    print(f"Table: {ENSEMBLE_TABLE}")
    print(f"Rows : {ensemble_rows}")
    print(f"Runtime table refreshed: {RUNTIME_TABLE}")
    print(f"Rows : {runtime_rows}")

    return ensemble


def main() -> None:
    print("=" * 38)
    print("SQLITE FOOTBALL ENSEMBLE ENGINE")
    print("=" * 38)
    export_football_ensemble_predictions()
    print("=" * 38)


if __name__ == "__main__":
    main()
