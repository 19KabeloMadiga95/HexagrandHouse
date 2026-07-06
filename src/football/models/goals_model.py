from __future__ import annotations

import pandas as pd

from src.football.models.sqlite_football_model_engine import (
    GOALS_TABLE,
    base_output_columns,
    clamp_probability,
    confidence_label,
    load_match_features,
    now_string,
    safe_float,
    save_model_table,
    sigmoid,
)


# =========================================================
# GOALS MODEL
# =========================================================

MODEL_NAME = "SQLite Goals Signal Model"
MODEL_VERSION = "football_goals_sqlite_v1"


def _expected_goals(row: pd.Series) -> tuple[float, float, float]:
    home_attack = safe_float(row.get("Home_GoalsFor_Last5"), safe_float(row.get("Home_GoalsFor_Last3"), 1.35))
    away_attack = safe_float(row.get("Away_GoalsFor_Last5"), safe_float(row.get("Away_GoalsFor_Last3"), 1.15))

    home_concede = safe_float(row.get("Home_GoalsAgainst_Last5"), safe_float(row.get("Home_GoalsAgainst_Last3"), 1.10))
    away_concede = safe_float(row.get("Away_GoalsAgainst_Last5"), safe_float(row.get("Away_GoalsAgainst_Last3"), 1.30))

    home_expected = (home_attack * 0.60) + (away_concede * 0.40)
    away_expected = (away_attack * 0.60) + (home_concede * 0.40)

    home_expected = max(home_expected, 0.15)
    away_expected = max(away_expected, 0.10)
    total_expected = home_expected + away_expected

    return round(home_expected, 3), round(away_expected, 3), round(total_expected, 3)


def _goals_probabilities(row: pd.Series, total_expected: float) -> tuple[float, float, float, float]:
    over15_base = sigmoid(total_expected, centre=1.80, scale=0.45)
    over25_base = sigmoid(total_expected, centre=2.55, scale=0.50)
    over35_base = sigmoid(total_expected, centre=3.35, scale=0.55)

    home_over25 = safe_float(row.get("Home_Over25Goals_Last5"), 0.50)
    away_over25 = safe_float(row.get("Away_Over25Goals_Last5"), 0.50)
    over25_form = (home_over25 + away_over25) / 2

    home_btts = safe_float(row.get("Home_BTTS_Last5"), 0.50)
    away_btts = safe_float(row.get("Away_BTTS_Last5"), 0.50)
    btts_form = (home_btts + away_btts) / 2

    over15 = clamp_probability((over15_base * 0.75) + (over25_form * 0.25))
    over25 = clamp_probability((over25_base * 0.70) + (over25_form * 0.30))
    over35 = clamp_probability((over35_base * 0.80) + (over25_form * 0.20))
    btts = clamp_probability((sigmoid(total_expected, centre=2.30, scale=0.65) * 0.45) + (btts_form * 0.55))

    return round(over15, 4), round(over25, 4), round(over35, 4), round(btts, 4)


def _best_goals_signal(over15: float, over25: float, over35: float, btts: float) -> tuple[str, str, float]:
    candidates = [
        ("Goals", "Over 1.5 Goals", over15),
        ("Goals", "Over 2.5 Goals", over25),
        ("Goals", "Over 3.5 Goals", over35),
        ("Goals", "BTTS Yes", btts),
    ]

    best_market, best_signal, best_probability = max(candidates, key=lambda item: item[2])
    return best_market, best_signal, round(best_probability, 4)


def build_goals_predictions() -> pd.DataFrame:
    df = load_match_features()

    if df.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    generated_at = now_string()

    for _, row in df.iterrows():
        home_expected, away_expected, total_expected = _expected_goals(row)
        over15, over25, over35, btts = _goals_probabilities(row, total_expected)
        market, signal, probability = _best_goals_signal(over15, over25, over35, btts)

        output = row.to_dict()
        output.update(
            {
                "ModelName": MODEL_NAME,
                "ModelVersion": MODEL_VERSION,
                "Market": market,
                "PrimaryMarketSignal": signal,
                "GoalsSignal": signal,
                "HomeExpectedGoals": home_expected,
                "AwayExpectedGoals": away_expected,
                "ExpectedTotalGoals": total_expected,
                "Over15GoalsProbability": over15,
                "Over25GoalsProbability": over25,
                "Over35GoalsProbability": over35,
                "BTTSProbability": btts,
                "ModelProbability": probability,
                "ConfidenceScore": probability,
                "ConfidenceLabel": confidence_label(probability),
                "ElitePrediction": 1 if probability >= 0.85 else 0,
                "GeneratedAt": generated_at,
            }
        )
        rows.append(output)

    out = pd.DataFrame(rows)

    preferred_columns = base_output_columns() + [
        "ModelName",
        "ModelVersion",
        "Market",
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
        "ConfidenceScore",
        "ConfidenceLabel",
        "ElitePrediction",
        "GeneratedAt",
    ]

    columns = [col for col in preferred_columns if col in out.columns]
    extra_columns = [col for col in out.columns if col not in columns]

    return out[columns + extra_columns]


def export_goals_predictions() -> pd.DataFrame:
    predictions = build_goals_predictions()
    rows = save_model_table(GOALS_TABLE, predictions)

    print("\nSQLite football goals model refreshed.")
    print(f"Table: {GOALS_TABLE}")
    print(f"Rows : {rows}")

    return predictions


def main() -> None:
    print("=" * 38)
    print("SQLITE FOOTBALL GOALS MODEL")
    print("=" * 38)
    export_goals_predictions()
    print("=" * 38)


if __name__ == "__main__":
    main()
