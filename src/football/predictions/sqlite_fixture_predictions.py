from __future__ import annotations

from datetime import datetime
from math import exp
from typing import Any

import pandas as pd

from src.data.sqlite_store import create_indexes, read_sqlite_table, replace_sqlite_table


# =========================================================
# UPCOMING FIXTURE PREDICTIONS - SQLITE RUNTIME
# =========================================================

FIXTURES_TABLE = "football_fixtures"
TEAM_FEATURES_TABLE = "football_team_features"
FIXTURE_PREDICTIONS_TABLE = "football_fixture_predictions"
RUNTIME_PREDICTIONS_TABLE = "football_predictions"
SUMMARY_TABLE = "football_fixture_prediction_summary"

MODEL_NAME = "SQLite Fixture Picks"
MODEL_VERSION = "football_fixture_sqlite_v1"

PREDICTION_COLUMNS = [
    "MatchKey",
    "FixtureKey",
    "MatchDate",
    "FixtureDate",
    "KickoffTime",
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
    "HomeWinProbability",
    "DrawProbability",
    "AwayWinProbability",
    "HomeExpectedGoals",
    "AwayExpectedGoals",
    "ExpectedTotalGoals",
    "Over15GoalsProbability",
    "Over25GoalsProbability",
    "BTTSProbability",
    "ExpectedTotalCorners",
    "Over95CornersProbability",
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
    "SourceName",
    "SourceUrl",
]


def _empty_predictions() -> pd.DataFrame:
    return pd.DataFrame(columns=PREDICTION_COLUMNS)


def _ensure_prediction_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return _empty_predictions()
    out = df.copy()
    for col in PREDICTION_COLUMNS:
        if col not in out.columns:
            out[col] = None
    return out[PREDICTION_COLUMNS]


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def sigmoid(value: float, centre: float = 0.0, scale: float = 1.0) -> float:
    try:
        z = (float(value) - centre) / max(float(scale), 0.0001)
        z = max(min(z, 12), -12)
        return 1 / (1 + exp(-z))
    except Exception:
        return 0.5


def confidence_label(probability: float) -> str:
    if probability >= 0.85:
        return "Elite"
    if probability >= 0.75:
        return "Strong"
    if probability >= 0.65:
        return "Medium"
    if probability >= 0.55:
        return "Small"
    return "Watch"


def normalize_three(home: float, draw: float, away: float) -> tuple[float, float, float]:
    home = max(float(home), 0.001)
    draw = max(float(draw), 0.001)
    away = max(float(away), 0.001)
    total = home + draw + away
    return round(home / total, 4), round(draw / total, 4), round(away / total, 4)


def _load_fixtures() -> pd.DataFrame:
    df = read_sqlite_table(FIXTURES_TABLE)
    if df.empty:
        return pd.DataFrame()

    out = df.copy()
    out["FixtureDate"] = pd.to_datetime(out["FixtureDate"], errors="coerce")
    today = pd.Timestamp(datetime.now().date())

    out = out[out["FixtureDate"].notna() & (out["FixtureDate"] >= today)].copy()
    return out.sort_values(["FixtureDate", "League", "HomeTeam", "AwayTeam"]).reset_index(drop=True)


def _load_latest_team_features() -> pd.DataFrame:
    df = read_sqlite_table(TEAM_FEATURES_TABLE)
    if df.empty:
        return pd.DataFrame()

    out = df.copy()
    out["MatchDate"] = pd.to_datetime(out.get("MatchDate"), errors="coerce")
    out = out[out["Team"].notna()].copy()

    sort_cols = [col for col in ["LeagueCode", "Team", "MatchDate"] if col in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols)

    group_cols = [col for col in ["LeagueCode", "Team"] if col in out.columns]
    if not group_cols:
        return pd.DataFrame()

    latest = out.groupby(group_cols, dropna=False).tail(1).copy()
    return latest.reset_index(drop=True)


def _feature_lookup(team_features: pd.DataFrame) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    if team_features.empty:
        return lookup

    for _, row in team_features.iterrows():
        key = (str(row.get("LeagueCode", "")).strip(), str(row.get("Team", "")).strip())
        lookup[key] = row.to_dict()

    return lookup


def _team_row(lookup: dict[tuple[str, str], dict[str, Any]], league_code: Any, team: Any) -> dict[str, Any]:
    return lookup.get((str(league_code).strip(), str(team).strip()), {})


def _metric(row: dict[str, Any], name: str, default: float) -> float:
    return safe_float(row.get(name), default)


def _home_away_probabilities(home: dict[str, Any], away: dict[str, Any]) -> tuple[float, float, float]:
    home_form = _metric(home, "FormPoints_Last5", 1.35)
    away_form = _metric(away, "FormPoints_Last5", 1.20)
    home_goal_diff = _metric(home, "GoalDifference_Last5", 0.0)
    away_goal_diff = _metric(away, "GoalDifference_Last5", 0.0)

    strength_diff = (home_form - away_form) + (home_goal_diff - away_goal_diff) * 0.35 + 0.18

    home_raw = sigmoid(strength_diff, centre=0.10, scale=1.35)
    away_raw = sigmoid(-strength_diff, centre=0.18, scale=1.35)
    draw_raw = clamp(0.28 - abs(strength_diff) * 0.035, 0.18, 0.32)

    return normalize_three(home_raw, draw_raw, away_raw)


def _expected_goals(home: dict[str, Any], away: dict[str, Any]) -> tuple[float, float, float]:
    home_gf = _metric(home, "GoalsFor_Last5", 1.25)
    home_ga = _metric(home, "GoalsAgainst_Last5", 1.15)
    away_gf = _metric(away, "GoalsFor_Last5", 1.10)
    away_ga = _metric(away, "GoalsAgainst_Last5", 1.25)

    home_xg = 1.05 + (home_gf - 1.20) * 0.45 + (away_ga - 1.20) * 0.35 + 0.18
    away_xg = 0.95 + (away_gf - 1.10) * 0.45 + (home_ga - 1.15) * 0.35

    home_xg = clamp(home_xg, 0.35, 3.20)
    away_xg = clamp(away_xg, 0.25, 3.00)
    return round(home_xg, 3), round(away_xg, 3), round(home_xg + away_xg, 3)


def _expected_corners(home: dict[str, Any], away: dict[str, Any]) -> float:
    home_cf = _metric(home, "CornersFor_Last5", 4.8)
    away_cf = _metric(away, "CornersFor_Last5", 4.3)
    home_ca = _metric(home, "CornersAgainst_Last5", 4.4)
    away_ca = _metric(away, "CornersAgainst_Last5", 4.7)

    expected = (home_cf + away_cf + home_ca + away_ca) / 2
    return round(clamp(expected, 5.0, 14.0), 3)


def _pick_signal(
    home_prob: float,
    draw_prob: float,
    away_prob: float,
    expected_total_goals: float,
    btts_prob: float,
    over15_prob: float,
    over25_prob: float,
    over95_corners_prob: float,
) -> dict[str, Any]:
    result_candidates = [
        ("Home Win", home_prob, "H"),
        ("Draw", draw_prob, "D"),
        ("Away Win", away_prob, "A"),
    ]
    result_label, result_prob, predicted_result = max(result_candidates, key=lambda item: item[1])

    candidates = [
        {"Market": "Result", "PrimaryMarketSignal": result_label, "PredictedResult": predicted_result, "Probability": result_prob},
        {"Market": "Goals", "PrimaryMarketSignal": "Over 1.5 Goals", "PredictedResult": None, "Probability": over15_prob},
        {"Market": "Goals", "PrimaryMarketSignal": "Over 2.5 Goals", "PredictedResult": None, "Probability": over25_prob},
        {"Market": "Goals", "PrimaryMarketSignal": "BTTS Yes", "PredictedResult": None, "Probability": btts_prob},
        {"Market": "Corners", "PrimaryMarketSignal": "Over 9.5 Corners", "PredictedResult": None, "Probability": over95_corners_prob},
    ]

    # Avoid fake 100% signals. Fixture predictions are directional picks, not certainties.
    best = max(candidates, key=lambda item: item["Probability"])
    best["Probability"] = round(clamp(best["Probability"], 0.50, 0.88), 4)
    return best


def build_fixture_predictions() -> pd.DataFrame:
    fixtures = _load_fixtures()
    team_features = _load_latest_team_features()

    if fixtures.empty:
        return _empty_predictions()

    lookup = _feature_lookup(team_features)
    generated_at = now_string()
    rows: list[dict[str, Any]] = []

    for _, fixture in fixtures.iterrows():
        league_code = fixture.get("LeagueCode")
        home_team = fixture.get("HomeTeam")
        away_team = fixture.get("AwayTeam")

        home = _team_row(lookup, league_code, home_team)
        away = _team_row(lookup, league_code, away_team)

        home_prob, draw_prob, away_prob = _home_away_probabilities(home, away)
        home_xg, away_xg, total_xg = _expected_goals(home, away)
        total_corners = _expected_corners(home, away)

        over15_prob = round(clamp(sigmoid(total_xg, centre=1.65, scale=0.75), 0.45, 0.88), 4)
        over25_prob = round(clamp(sigmoid(total_xg, centre=2.55, scale=0.70), 0.35, 0.82), 4)
        btts_prob = round(clamp(sigmoid(min(home_xg, away_xg), centre=0.88, scale=0.45), 0.35, 0.80), 4)
        over95_corners_prob = round(clamp(sigmoid(total_corners, centre=9.5, scale=1.55), 0.35, 0.82), 4)

        pick = _pick_signal(
            home_prob,
            draw_prob,
            away_prob,
            total_xg,
            btts_prob,
            over15_prob,
            over25_prob,
            over95_corners_prob,
        )
        probability = float(pick["Probability"])

        fixture_date = pd.to_datetime(fixture.get("FixtureDate"), errors="coerce")
        date_key = fixture_date.strftime("%Y-%m-%d") if pd.notna(fixture_date) else "unknown-date"
        match_key = fixture.get("FixtureKey") or f"{league_code}_{date_key}_{home_team}_{away_team}"

        rows.append(
            {
                "MatchKey": match_key,
                "FixtureKey": fixture.get("FixtureKey"),
                "MatchDate": fixture_date,
                "FixtureDate": fixture_date,
                "KickoffTime": fixture.get("KickoffTime"),
                "LeagueCode": league_code,
                "League": fixture.get("League"),
                "Country": fixture.get("Country"),
                "Tier": fixture.get("Tier"),
                "HomeTeam": home_team,
                "AwayTeam": away_team,
                "HomeGoals": None,
                "AwayGoals": None,
                "TotalGoals": None,
                "HomeCorners": None,
                "AwayCorners": None,
                "TotalCorners": None,
                "Result": None,
                "ResultLabel": None,
                "ModelName": MODEL_NAME,
                "ModelVersion": MODEL_VERSION,
                "SourceModel": "Fixture",
                "Market": pick["Market"],
                "PrimaryMarketSignal": pick["PrimaryMarketSignal"],
                "PredictedResult": pick["PredictedResult"],
                "HomeWinProbability": home_prob,
                "DrawProbability": draw_prob,
                "AwayWinProbability": away_prob,
                "HomeExpectedGoals": home_xg,
                "AwayExpectedGoals": away_xg,
                "ExpectedTotalGoals": total_xg,
                "Over15GoalsProbability": over15_prob,
                "Over25GoalsProbability": over25_prob,
                "BTTSProbability": btts_prob,
                "ExpectedTotalCorners": total_corners,
                "Over95CornersProbability": over95_corners_prob,
                "ModelProbability": probability,
                "ConfidenceScore": probability,
                "EnsembleConfidenceScore": probability,
                "ConfidenceLabel": confidence_label(probability),
                "SignalLabel": confidence_label(probability),
                "ElitePrediction": 1 if probability >= 0.85 else 0,
                "ValueScore": round(probability * 100, 2),
                "ValueRating": confidence_label(probability),
                "PredictionHit": None,
                "GeneratedAt": generated_at,
                "SourceName": fixture.get("SourceName", "football-data.co.uk fixtures"),
                "SourceUrl": fixture.get("SourceUrl"),
            }
        )

    out = _ensure_prediction_columns(pd.DataFrame(rows))
    if not out.empty:
        out = out.sort_values(["MatchDate", "EnsembleConfidenceScore"], ascending=[True, False]).reset_index(drop=True)

    return out


def build_summary(predictions: pd.DataFrame) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame(
            [
                {
                    "Metric": "FixturePredictions",
                    "Value": 0,
                    "Detail": "No upcoming fixtures available from the public source.",
                    "UpdatedAt": now_string(),
                }
            ]
        )

    return pd.DataFrame(
        [
            {"Metric": "FixturePredictions", "Value": int(len(predictions)), "Detail": "Rows in football_fixture_predictions", "UpdatedAt": now_string()},
            {"Metric": "Leagues", "Value": int(predictions["League"].nunique()), "Detail": "Distinct leagues", "UpdatedAt": now_string()},
            {"Metric": "EarliestFixture", "Value": str(pd.to_datetime(predictions["MatchDate"]).min().date()), "Detail": "Next fixture date", "UpdatedAt": now_string()},
            {"Metric": "LatestFixture", "Value": str(pd.to_datetime(predictions["MatchDate"]).max().date()), "Detail": "Last fixture date in window", "UpdatedAt": now_string()},
            {"Metric": "AverageConfidence", "Value": round(float(predictions["EnsembleConfidenceScore"].mean()), 4), "Detail": "Average fixture pick confidence", "UpdatedAt": now_string()},
        ]
    )


def export_fixture_predictions() -> pd.DataFrame:
    predictions = build_fixture_predictions()

    fixture_rows = replace_sqlite_table(FIXTURE_PREDICTIONS_TABLE, predictions)

    # Runtime football_predictions should represent current/future website picks.
    # Historical model outputs remain in football_ensemble_predictions and reporting tables.
    runtime_rows = replace_sqlite_table(RUNTIME_PREDICTIONS_TABLE, predictions)

    replace_sqlite_table(SUMMARY_TABLE, build_summary(predictions))

    for table in [FIXTURE_PREDICTIONS_TABLE, RUNTIME_PREDICTIONS_TABLE]:
        create_indexes(
            table,
            ["MatchKey", "FixtureKey", "MatchDate", "League", "LeagueCode", "HomeTeam", "AwayTeam", "Market", "ConfidenceLabel", "GeneratedAt"],
        )
    create_indexes(SUMMARY_TABLE, ["Metric", "UpdatedAt"])

    print("\nSQLite football fixture predictions refreshed.")
    print(f"Table: {FIXTURE_PREDICTIONS_TABLE}")
    print(f"Rows : {fixture_rows}")
    print(f"Runtime table refreshed: {RUNTIME_PREDICTIONS_TABLE}")
    print(f"Rows : {runtime_rows}")
    print("=" * 38)

    return predictions


def main() -> pd.DataFrame:
    return export_fixture_predictions()


if __name__ == "__main__":
    main()
