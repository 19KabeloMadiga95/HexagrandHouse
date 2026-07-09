from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.data.sqlite_store import create_indexes, read_sqlite_table, replace_sqlite_table


# =========================================================
# SQLITE TOP PLAYS REPORT
# =========================================================

SOURCE_TABLE = "football_fixture_predictions"
TOP_PLAYS_TABLE = "football_top_plays"
SUMMARY_TABLE = "football_top_plays_summary"
LEAGUE_TABLE = "football_top_plays_by_league"
MARKET_TABLE = "football_top_plays_by_market"
RATING_TABLE = "football_top_plays_by_rating"
NOTES_TABLE = "football_top_plays_notes"

DEFAULT_LIMIT = 500

TOP_PLAY_COLUMNS = [
    "TopPlayRank",
    "MatchKey",
    "MatchDate",
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
    "TopPlayScore",
    "RankReason",
    "PredictionHit",
    "GeneratedAt",
    "ReportGeneratedAt",
]

GROUP_SUMMARY_COLUMNS = [
    "TopPlayCount",
    "AverageTopPlayScore",
    "BestTopPlayScore",
    "EliteCount",
    "UpdatedAt",
]

SUMMARY_COLUMNS = ["Metric", "Value", "Detail", "UpdatedAt"]
NOTES_COLUMNS = ["NoteType", "Note", "UpdatedAt"]


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def empty_top_plays() -> pd.DataFrame:
    """Return an empty dataframe with a stable schema.

    This is important because pandas cannot replace a SQLite table from a
    zero-column dataframe. Without this, old football_top_plays/value tables
    can survive when there are no upcoming fixtures.
    """

    return pd.DataFrame(columns=TOP_PLAY_COLUMNS)


def empty_group_summary(group_col: str) -> pd.DataFrame:
    return pd.DataFrame(columns=[group_col] + GROUP_SUMMARY_COLUMNS)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _clean(df: pd.DataFrame) -> pd.DataFrame:
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
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    if "EnsembleConfidenceScore" not in out.columns:
        if "ConfidenceScore" in out.columns:
            out["EnsembleConfidenceScore"] = out["ConfidenceScore"]
        elif "ModelProbability" in out.columns:
            out["EnsembleConfidenceScore"] = out["ModelProbability"]
        else:
            out["EnsembleConfidenceScore"] = 0

    if "ValueScore" not in out.columns:
        out["ValueScore"] = out["EnsembleConfidenceScore"] * 100

    return out


def load_predictions() -> pd.DataFrame:
    return _clean(read_sqlite_table(SOURCE_TABLE))


def _summary_metric(metric: str, value: Any, detail: str) -> dict[str, Any]:
    return {
        "Metric": metric,
        "Value": value,
        "Detail": detail,
        "UpdatedAt": now_string(),
    }


def build_top_plays(limit: int = DEFAULT_LIMIT) -> pd.DataFrame:
    df = load_predictions()

    if df.empty:
        return empty_top_plays()

    out = df.copy()

    if "PrimaryMarketSignal" not in out.columns:
        out["PrimaryMarketSignal"] = out.get("Market", "No Signal")

    if "ConfidenceLabel" not in out.columns:
        out["ConfidenceLabel"] = "Unrated"

    if "Market" not in out.columns:
        out["Market"] = "Unknown"

    out["TopPlayScore"] = (
        pd.to_numeric(out["EnsembleConfidenceScore"], errors="coerce").fillna(0) * 100
    ).round(2)

    out["RankReason"] = out.apply(
        lambda row: f"{row.get('ConfidenceLabel', 'Signal')} signal at {safe_float(row.get('TopPlayScore'), 0):.2f}",
        axis=1,
    )

    sort_cols = ["TopPlayScore"]
    ascending = [False]

    if "MatchDate" in out.columns:
        sort_cols.append("MatchDate")
        ascending.append(False)

    out = out.sort_values(sort_cols, ascending=ascending).head(limit).copy()
    out.insert(0, "TopPlayRank", range(1, len(out) + 1))
    out["ReportGeneratedAt"] = now_string()

    columns = [col for col in TOP_PLAY_COLUMNS if col in out.columns]
    extras = [col for col in out.columns if col not in columns]
    return out[columns + extras].reset_index(drop=True)


def _group_summary(top_df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if top_df.empty or group_col not in top_df.columns:
        return empty_group_summary(group_col)

    rows: list[dict[str, Any]] = []

    for key, grp in top_df.groupby(group_col, dropna=False):
        rows.append(
            {
                group_col: key,
                "TopPlayCount": int(len(grp)),
                "AverageTopPlayScore": round(float(pd.to_numeric(grp["TopPlayScore"], errors="coerce").mean()), 2),
                "BestTopPlayScore": round(float(pd.to_numeric(grp["TopPlayScore"], errors="coerce").max()), 2),
                "EliteCount": int((grp.get("ConfidenceLabel", pd.Series(dtype=str)).astype(str).str.lower() == "elite").sum()),
                "UpdatedAt": now_string(),
            }
        )

    out = pd.DataFrame(rows)
    return out.sort_values(["TopPlayCount", "BestTopPlayScore"], ascending=[False, False]).reset_index(drop=True)


def build_summary(top_df: pd.DataFrame) -> pd.DataFrame:
    if top_df.empty:
        return pd.DataFrame([_summary_metric("TopPlays", 0, "No current top plays generated")], columns=SUMMARY_COLUMNS)

    return pd.DataFrame(
        [
            _summary_metric("TopPlays", int(len(top_df)), "Rows in football_top_plays"),
            _summary_metric("Leagues", int(top_df["League"].nunique()) if "League" in top_df.columns else 0, "Distinct leagues in top plays"),
            _summary_metric("Markets", int(top_df["Market"].nunique()) if "Market" in top_df.columns else 0, "Distinct markets in top plays"),
            _summary_metric("AverageTopPlayScore", round(float(pd.to_numeric(top_df["TopPlayScore"], errors="coerce").mean()), 2), "Average top-play score"),
            _summary_metric("BestTopPlayScore", round(float(pd.to_numeric(top_df["TopPlayScore"], errors="coerce").max()), 2), "Highest top-play score"),
        ],
        columns=SUMMARY_COLUMNS,
    )


def build_notes() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "NoteType": "Source",
                "Note": "Top plays are ranked from current/future fixture predictions in SQLite.",
                "UpdatedAt": now_string(),
            },
            {
                "NoteType": "Runtime",
                "Note": "When there are no upcoming fixtures, this process writes an empty current table so stale rows are removed.",
                "UpdatedAt": now_string(),
            },
        ],
        columns=NOTES_COLUMNS,
    )


def export_top_plays_report(limit: int = DEFAULT_LIMIT) -> dict[str, int]:
    top_df = build_top_plays(limit=limit)

    outputs = {
        TOP_PLAYS_TABLE: top_df,
        SUMMARY_TABLE: build_summary(top_df),
        LEAGUE_TABLE: _group_summary(top_df, "League"),
        MARKET_TABLE: _group_summary(top_df, "Market"),
        RATING_TABLE: _group_summary(top_df, "ConfidenceLabel"),
        NOTES_TABLE: build_notes(),
    }

    row_counts: dict[str, int] = {}
    for table_name, df in outputs.items():
        row_counts[table_name] = replace_sqlite_table(table_name, df)

    create_indexes(TOP_PLAYS_TABLE, ["TopPlayRank", "MatchDate", "League", "Market", "ConfidenceLabel", "GeneratedAt"])
    create_indexes(LEAGUE_TABLE, ["League", "UpdatedAt"])
    create_indexes(MARKET_TABLE, ["Market", "UpdatedAt"])
    create_indexes(RATING_TABLE, ["ConfidenceLabel", "UpdatedAt"])

    print("\nSQLite top plays report tables refreshed.")
    for table_name, rows in row_counts.items():
        print(f"{table_name}: {rows}")
    print("=" * 38)

    return row_counts


def main() -> dict[str, int]:
    print("=" * 38)
    print("SQLITE FOOTBALL TOP PLAYS REPORT")
    print("=" * 38)
    return export_top_plays_report()


if __name__ == "__main__":
    main()
