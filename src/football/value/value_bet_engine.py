from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.data.sqlite_store import create_indexes, read_sqlite_table, replace_sqlite_table


# =========================================================
# SQLITE VALUE BET ENGINE
# =========================================================

SOURCE_TABLE = "football_fixture_predictions"
VALUE_TABLE = "football_value_bets"
DETAIL_TABLE = "football_value_bet_details"
SUMMARY_TABLE = "football_value_bet_summary"
RATING_TABLE = "football_value_bets_by_rating"
LEAGUE_TABLE = "football_value_bets_by_league"
NOTES_TABLE = "football_value_bet_notes"

DEFAULT_LIMIT = 1000

VALUE_BET_COLUMNS = [
    "ValueRank",
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
    "ConfidenceLabel",
    "FairOdds",
    "MinimumValueOdds",
    "BookmakerOdds",
    "Bookmaker",
    "ModelEdgePct",
    "ValueBetScore",
    "ValueRating",
    "ValueBetType",
    "HasBookmakerOdds",
    "PredictionHit",
    "GeneratedAt",
    "ValueGeneratedAt",
]

GROUP_SUMMARY_COLUMNS = [
    "ValueBetCount",
    "AverageValueBetScore",
    "BestValueBetScore",
    "AverageModelProbability",
    "BestModelEdgePct",
    "UpdatedAt",
]

SUMMARY_COLUMNS = ["Metric", "Value", "Detail", "UpdatedAt"]
NOTES_COLUMNS = ["NoteType", "Note", "UpdatedAt"]


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def empty_value_bets() -> pd.DataFrame:
    """Return an empty dataframe with a stable schema.

    The reporting cycle must overwrite old value rows even when there are no
    current fixture predictions. A zero-column dataframe can fail to replace a
    SQLite table, leaving stale rows behind.
    """

    return pd.DataFrame(columns=VALUE_BET_COLUMNS)


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

    return out


def load_predictions() -> pd.DataFrame:
    return _clean(read_sqlite_table(SOURCE_TABLE))


def value_rating(edge_pct: float, probability: float) -> str:
    if probability >= 0.85 and edge_pct >= 15:
        return "Elite"

    if probability >= 0.75 and edge_pct >= 10:
        return "Strong"

    if probability >= 0.68 and edge_pct >= 6:
        return "Medium"

    if probability >= 0.60:
        return "Watchlist"

    return "No Value"


def _minimum_odds(probability: float, margin: float = 0.05) -> float | None:
    probability = max(min(probability, 0.99), 0.01)
    fair_odds = 1 / probability
    return round(fair_odds * (1 + margin), 3)


# =========================================================
# BUILDERS
# =========================================================

def build_value_bets(limit: int = DEFAULT_LIMIT) -> pd.DataFrame:
    df = load_predictions()

    if df.empty:
        return empty_value_bets()

    out = df.copy()
    out["ModelProbability"] = pd.to_numeric(out["EnsembleConfidenceScore"], errors="coerce").fillna(0)

    # This is a model-only value proxy. It deliberately avoids pretending
    # bookmaker odds are present where the SQLite warehouse has none.
    out["FairOdds"] = out["ModelProbability"].apply(lambda p: round(1 / max(float(p), 0.01), 3))
    out["MinimumValueOdds"] = out["ModelProbability"].apply(_minimum_odds)
    out["ModelEdgePct"] = ((out["ModelProbability"] - 0.55).clip(lower=0) * 100).round(2)
    out["ValueBetType"] = "Model-only edge proxy"
    out["HasBookmakerOdds"] = 0
    out["BookmakerOdds"] = None
    out["Bookmaker"] = "Not supplied"
    out["ValueRating"] = out.apply(
        lambda row: value_rating(
            safe_float(row.get("ModelEdgePct"), 0),
            safe_float(row.get("ModelProbability"), 0),
        ),
        axis=1,
    )
    out["ValueBetScore"] = (out["ModelProbability"] * 100 + out["ModelEdgePct"]).round(2)
    out["ValueGeneratedAt"] = now_string()

    out = out[out["ValueRating"] != "No Value"].copy()
    if out.empty:
        return empty_value_bets()

    out = out.sort_values(["ValueBetScore", "ModelProbability"], ascending=[False, False]).head(limit)
    out.insert(0, "ValueRank", range(1, len(out) + 1))

    columns = [col for col in VALUE_BET_COLUMNS if col in out.columns]
    extras = [col for col in out.columns if col not in columns]

    return out[columns + extras].reset_index(drop=True)


def _group_summary(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if df.empty or group_col not in df.columns:
        return empty_group_summary(group_col)

    rows: list[dict[str, Any]] = []

    for key, grp in df.groupby(group_col, dropna=False):
        rows.append(
            {
                group_col: key,
                "ValueBetCount": int(len(grp)),
                "AverageValueBetScore": round(float(pd.to_numeric(grp["ValueBetScore"], errors="coerce").mean()), 2),
                "BestValueBetScore": round(float(pd.to_numeric(grp["ValueBetScore"], errors="coerce").max()), 2),
                "AverageModelProbability": round(float(pd.to_numeric(grp["ModelProbability"], errors="coerce").mean()), 4),
                "BestModelEdgePct": round(float(pd.to_numeric(grp["ModelEdgePct"], errors="coerce").max()), 2),
                "UpdatedAt": now_string(),
            }
        )

    out = pd.DataFrame(rows)
    return out.sort_values(["ValueBetCount", "BestValueBetScore"], ascending=[False, False]).reset_index(drop=True)


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            [
                {
                    "Metric": "ValueBets",
                    "Value": 0,
                    "Detail": "No current model-only value rows generated",
                    "UpdatedAt": now_string(),
                }
            ],
            columns=SUMMARY_COLUMNS,
        )

    return pd.DataFrame(
        [
            {"Metric": "ValueBets", "Value": int(len(df)), "Detail": "Rows in football_value_bets", "UpdatedAt": now_string()},
            {"Metric": "Leagues", "Value": int(df["League"].nunique()) if "League" in df.columns else 0, "Detail": "Distinct leagues", "UpdatedAt": now_string()},
            {"Metric": "Markets", "Value": int(df["Market"].nunique()) if "Market" in df.columns else 0, "Detail": "Distinct markets", "UpdatedAt": now_string()},
            {"Metric": "AverageValueBetScore", "Value": round(float(pd.to_numeric(df["ValueBetScore"], errors="coerce").mean()), 2), "Detail": "Mean model-only value score", "UpdatedAt": now_string()},
            {"Metric": "BestValueBetScore", "Value": round(float(pd.to_numeric(df["ValueBetScore"], errors="coerce").max()), 2), "Detail": "Highest model-only value score", "UpdatedAt": now_string()},
            {"Metric": "BookmakerOddsCoverage", "Value": 0, "Detail": "Bookmaker odds are not yet supplied to SQLite", "UpdatedAt": now_string()},
        ],
        columns=SUMMARY_COLUMNS,
    )


def build_notes() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "NoteType": "Important",
                "Note": "These value rows are model-only edge proxies because bookmaker odds are not yet stored in SQLite.",
                "UpdatedAt": now_string(),
            },
            {
                "NoteType": "Current Data",
                "Note": "When there are no upcoming fixture predictions, this process writes an empty current table so stale rows are removed.",
                "UpdatedAt": now_string(),
            },
            {
                "NoteType": "Runtime",
                "Note": "The value engine reads football_fixture_predictions and writes SQLite tables only.",
                "UpdatedAt": now_string(),
            },
        ],
        columns=NOTES_COLUMNS,
    )


# =========================================================
# EXPORT
# =========================================================

def export_value_bets(limit: int = DEFAULT_LIMIT) -> dict[str, int]:
    value_df = build_value_bets(limit=limit)

    outputs = {
        VALUE_TABLE: value_df,
        DETAIL_TABLE: value_df.copy(),
        SUMMARY_TABLE: build_summary(value_df),
        RATING_TABLE: _group_summary(value_df, "ValueRating"),
        LEAGUE_TABLE: _group_summary(value_df, "League"),
        NOTES_TABLE: build_notes(),
    }

    row_counts: dict[str, int] = {}
    for table_name, df in outputs.items():
        row_counts[table_name] = replace_sqlite_table(table_name, df)

    create_indexes(VALUE_TABLE, ["ValueRank", "MatchDate", "League", "Market", "ValueRating", "GeneratedAt"])
    create_indexes(DETAIL_TABLE, ["ValueRank", "MatchDate", "League", "Market", "ValueRating", "GeneratedAt"])
    create_indexes(RATING_TABLE, ["ValueRating", "UpdatedAt"])
    create_indexes(LEAGUE_TABLE, ["League", "UpdatedAt"])

    print("\nSQLite football value tables refreshed.")
    for table_name, rows in row_counts.items():
        print(f"{table_name}: {rows}")
    print("=" * 38)

    return row_counts


def main() -> dict[str, int]:
    print("=" * 38)
    print("SQLITE FOOTBALL VALUE BET ENGINE")
    print("=" * 38)
    return export_value_bets()


if __name__ == "__main__":
    main()
