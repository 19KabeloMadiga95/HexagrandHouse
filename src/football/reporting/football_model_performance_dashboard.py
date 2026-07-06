from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.data.sqlite_store import create_indexes, read_sqlite_table, replace_sqlite_table


# =========================================================
# SQLITE FOOTBALL PERFORMANCE REPORTING
# =========================================================

SOURCE_TABLE = "football_ensemble_predictions"
BACKTEST_TABLE = "football_backtest_history"
DASHBOARD_TABLE = "football_performance_dashboard_summary"
KPI_TABLE = "football_performance_kpis"
LEAGUE_TABLE = "football_league_performance"
MARKET_TABLE = "football_market_performance"
GRADE_TABLE = "football_grade_summary"
STATUS_TABLE = "football_file_status"
NOTES_TABLE = "football_performance_notes"

MODEL_TABLES = [
    "football_match_features",
    "football_result_model_predictions",
    "football_goals_model_predictions",
    "football_corners_model_predictions",
    "football_ensemble_predictions",
    "football_predictions",
]


# =========================================================
# HELPERS
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


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def percentage(value: Any) -> float:
    return round(safe_float(value, 0.0) * 100, 2)


def _first_existing(df: pd.DataFrame, candidates: list[str], default: Any = None) -> pd.Series:
    for col in candidates:
        if col in df.columns:
            return df[col]
    return pd.Series([default] * len(df), index=df.index)


def _clean_predictions(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    out = df.copy()

    if "MatchDate" in out.columns:
        out["MatchDate"] = pd.to_datetime(out["MatchDate"], errors="coerce")

    if "GeneratedAt" in out.columns:
        out["GeneratedAt"] = pd.to_datetime(out["GeneratedAt"], errors="coerce")

    for col in [
        "ModelProbability",
        "ConfidenceScore",
        "EnsembleConfidenceScore",
        "ValueScore",
        "PredictionHit",
        "ElitePrediction",
        "HomeGoals",
        "AwayGoals",
        "TotalGoals",
        "HomeCorners",
        "AwayCorners",
        "TotalCorners",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    if "ConfidenceScore" not in out.columns:
        out["ConfidenceScore"] = _first_existing(
            out,
            ["EnsembleConfidenceScore", "ModelProbability"],
            0,
        )

    if "EnsembleConfidenceScore" not in out.columns:
        out["EnsembleConfidenceScore"] = _first_existing(
            out,
            ["ConfidenceScore", "ModelProbability"],
            0,
        )

    if "PredictionHit" in out.columns:
        out["PredictionHit"] = pd.to_numeric(out["PredictionHit"], errors="coerce")

    return out


def load_predictions() -> pd.DataFrame:
    return _clean_predictions(read_sqlite_table(SOURCE_TABLE))


def _hit_rate(df: pd.DataFrame) -> float | None:
    if df.empty or "PredictionHit" not in df.columns:
        return None

    hit = pd.to_numeric(df["PredictionHit"], errors="coerce")
    hit = hit[hit.notna()]

    if hit.empty:
        return None

    return round(float(hit.mean()), 4)


def _latest_date(df: pd.DataFrame, column: str) -> str:
    if df.empty or column not in df.columns:
        return ""

    value = pd.to_datetime(df[column], errors="coerce").max()
    if pd.isna(value):
        return ""

    return value.strftime("%Y-%m-%d %H:%M:%S")


def _top_value_counts(df: pd.DataFrame, column: str, limit: int = 1) -> str:
    if df.empty or column not in df.columns:
        return ""

    counts = df[column].dropna().astype(str).value_counts().head(limit)
    if counts.empty:
        return ""

    return ", ".join([f"{idx} ({val})" for idx, val in counts.items()])


def _table_status(table_name: str) -> dict[str, Any]:
    df = read_sqlite_table(table_name)
    latest_generated = _latest_date(df, "GeneratedAt")
    latest_match = _latest_date(df, "MatchDate")

    return {
        "TableName": table_name,
        "RowCount": int(len(df)),
        "LatestGeneratedAt": latest_generated,
        "LatestMatchDate": latest_match,
        "Status": "Available" if not df.empty else "Empty/Missing",
        "CheckedAt": now_string(),
    }


# =========================================================
# BUILDERS
# =========================================================

def build_backtest_history(predictions: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_predictions() if predictions is None else _clean_predictions(predictions)

    columns = [
        "MatchKey",
        "MatchDate",
        "Season",
        "LeagueCode",
        "League",
        "Country",
        "Tier",
        "HomeTeam",
        "AwayTeam",
        "Market",
        "PrimaryMarketSignal",
        "PredictedResult",
        "ModelProbability",
        "ConfidenceScore",
        "EnsembleConfidenceScore",
        "ConfidenceLabel",
        "ValueScore",
        "ValueRating",
        "PredictionHit",
        "HomeGoals",
        "AwayGoals",
        "TotalGoals",
        "HomeCorners",
        "AwayCorners",
        "TotalCorners",
        "GeneratedAt",
    ]

    if df.empty:
        return pd.DataFrame(columns=columns + ["BacktestStatus", "EvaluatedAt"])

    out = df[[col for col in columns if col in df.columns]].copy()

    if "PredictionHit" in out.columns:
        out = out[pd.to_numeric(out["PredictionHit"], errors="coerce").notna()].copy()

    out["BacktestStatus"] = "Evaluated"
    out["EvaluatedAt"] = now_string()

    if "MatchDate" in out.columns:
        out = out.sort_values("MatchDate", ascending=False)

    return out.reset_index(drop=True)


def build_dashboard_summary(predictions: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_predictions() if predictions is None else _clean_predictions(predictions)
    evaluated = build_backtest_history(df)
    generated = now_string()

    hit_rate = _hit_rate(evaluated)
    avg_conf = round(float(pd.to_numeric(df.get("EnsembleConfidenceScore", pd.Series(dtype=float)), errors="coerce").mean()), 4) if not df.empty else 0
    elite_count = int(pd.to_numeric(df.get("ElitePrediction", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not df.empty else 0

    rows = [
        {"Metric": "TotalSignals", "Value": int(len(df)), "DisplayValue": f"{len(df):,}", "Detail": "Rows in football_ensemble_predictions", "UpdatedAt": generated},
        {"Metric": "EvaluatedSignals", "Value": int(len(evaluated)), "DisplayValue": f"{len(evaluated):,}", "Detail": "Rows with a known PredictionHit", "UpdatedAt": generated},
        {"Metric": "HistoricalHitRate", "Value": hit_rate, "DisplayValue": "-" if hit_rate is None else f"{percentage(hit_rate)}%", "Detail": "Average hit rate across evaluated rows", "UpdatedAt": generated},
        {"Metric": "AverageConfidence", "Value": avg_conf, "DisplayValue": f"{percentage(avg_conf)}%", "Detail": "Mean ensemble confidence", "UpdatedAt": generated},
        {"Metric": "EliteSignals", "Value": elite_count, "DisplayValue": f"{elite_count:,}", "Detail": "Rows flagged as ElitePrediction", "UpdatedAt": generated},
        {"Metric": "LeaguesCovered", "Value": int(df["League"].nunique()) if "League" in df.columns and not df.empty else 0, "DisplayValue": str(int(df["League"].nunique())) if "League" in df.columns and not df.empty else "0", "Detail": "Distinct leagues", "UpdatedAt": generated},
        {"Metric": "TopMarket", "Value": None, "DisplayValue": _top_value_counts(df, "Market"), "Detail": "Most common market signal", "UpdatedAt": generated},
        {"Metric": "LatestMatchDate", "Value": None, "DisplayValue": _latest_date(df, "MatchDate"), "Detail": "Newest match date in signals", "UpdatedAt": generated},
        {"Metric": "LatestGeneratedAt", "Value": None, "DisplayValue": _latest_date(df, "GeneratedAt"), "Detail": "Newest model generation timestamp", "UpdatedAt": generated},
    ]

    return pd.DataFrame(rows)


def build_kpis(predictions: pd.DataFrame | None = None) -> pd.DataFrame:
    summary = build_dashboard_summary(predictions)
    if summary.empty:
        return pd.DataFrame(columns=["KPI", "Value", "DisplayValue", "UpdatedAt"])

    return summary.rename(columns={"Metric": "KPI"})[["KPI", "Value", "DisplayValue", "UpdatedAt"]].copy()


def _group_performance(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if df.empty or group_col not in df.columns:
        return pd.DataFrame()

    records: list[dict[str, Any]] = []

    for key, grp in df.groupby(group_col, dropna=False):
        hit_rate = _hit_rate(grp)
        avg_conf = round(float(pd.to_numeric(grp.get("EnsembleConfidenceScore", pd.Series(dtype=float)), errors="coerce").mean()), 4)
        elite_count = int(pd.to_numeric(grp.get("ElitePrediction", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())

        records.append(
            {
                group_col: key,
                "SignalCount": int(len(grp)),
                "EvaluatedCount": int(pd.to_numeric(grp.get("PredictionHit", pd.Series(dtype=float)), errors="coerce").notna().sum()) if "PredictionHit" in grp.columns else 0,
                "HitRate": hit_rate,
                "HitRatePct": None if hit_rate is None else percentage(hit_rate),
                "AverageConfidence": avg_conf,
                "AverageConfidencePct": percentage(avg_conf),
                "EliteSignals": elite_count,
                "TopMarket": _top_value_counts(grp, "Market"),
                "LatestMatchDate": _latest_date(grp, "MatchDate"),
                "UpdatedAt": now_string(),
            }
        )

    out = pd.DataFrame(records)
    if not out.empty:
        out = out.sort_values(["SignalCount", "AverageConfidence"], ascending=[False, False])

    return out.reset_index(drop=True)


def build_league_performance(predictions: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_predictions() if predictions is None else _clean_predictions(predictions)
    return _group_performance(df, "League")


def build_market_performance(predictions: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_predictions() if predictions is None else _clean_predictions(predictions)
    return _group_performance(df, "Market")


def build_grade_summary(predictions: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_predictions() if predictions is None else _clean_predictions(predictions)
    group_col = "ConfidenceLabel" if "ConfidenceLabel" in df.columns else "ValueRating"
    return _group_performance(df, group_col)


def build_file_status() -> pd.DataFrame:
    return pd.DataFrame([_table_status(table_name) for table_name in MODEL_TABLES])


def build_notes() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "NoteType": "Architecture",
                "Note": "Football performance reporting reads and writes SQLite tables only.",
                "UpdatedAt": now_string(),
            },
            {
                "NoteType": "Backtest",
                "Note": "football_backtest_history is generated from evaluated rows in football_ensemble_predictions.",
                "UpdatedAt": now_string(),
            },
            {
                "NoteType": "Runtime",
                "Note": "Excel files are no longer required for the football reporting runtime layer.",
                "UpdatedAt": now_string(),
            },
        ]
    )


# =========================================================
# EXPORT
# =========================================================

def export_football_model_performance_dashboard() -> dict[str, int]:
    predictions = load_predictions()

    outputs = {
        BACKTEST_TABLE: build_backtest_history(predictions),
        DASHBOARD_TABLE: build_dashboard_summary(predictions),
        KPI_TABLE: build_kpis(predictions),
        LEAGUE_TABLE: build_league_performance(predictions),
        MARKET_TABLE: build_market_performance(predictions),
        GRADE_TABLE: build_grade_summary(predictions),
        STATUS_TABLE: build_file_status(),
        NOTES_TABLE: build_notes(),
    }

    row_counts: dict[str, int] = {}

    for table_name, df in outputs.items():
        row_counts[table_name] = replace_sqlite_table(table_name, df)

    create_indexes(BACKTEST_TABLE, ["MatchKey", "MatchDate", "League", "Market", "ConfidenceLabel", "GeneratedAt"])
    create_indexes(LEAGUE_TABLE, ["League", "LatestMatchDate", "UpdatedAt"])
    create_indexes(MARKET_TABLE, ["Market", "LatestMatchDate", "UpdatedAt"])
    create_indexes(GRADE_TABLE, ["ConfidenceLabel", "ValueRating", "UpdatedAt"])
    create_indexes(STATUS_TABLE, ["TableName", "Status", "CheckedAt"])

    print("\nSQLite football performance reporting tables refreshed.")
    for table_name, rows in row_counts.items():
        print(f"{table_name}: {rows}")
    print("=" * 38)

    return row_counts


def main() -> dict[str, int]:
    print("=" * 38)
    print("SQLITE FOOTBALL MODEL PERFORMANCE")
    print("=" * 38)
    return export_football_model_performance_dashboard()


if __name__ == "__main__":
    main()
