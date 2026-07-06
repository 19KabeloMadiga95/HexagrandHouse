from __future__ import annotations

import pandas as pd

from src.football.models.sqlite_football_model_engine import (
    CORNERS_TABLE,
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
# CORNERS MODEL
# =========================================================

MODEL_NAME = "SQLite Corners Signal Model"
MODEL_VERSION = "football_corners_sqlite_v1"


def _expected_corners(row: pd.Series) -> tuple[float, float, float]:
    home_for = safe_float(row.get("Home_CornersFor_Last5"), safe_float(row.get("Home_CornersFor_Last3"), 5.0))
    away_for = safe_float(row.get("Away_CornersFor_Last5"), safe_float(row.get("Away_CornersFor_Last3"), 4.2))

    home_against = safe_float(row.get("Home_CornersAgainst_Last5"), safe_float(row.get("Home_CornersAgainst_Last3"), 4.2))
    away_against = safe_float(row.get("Away_CornersAgainst_Last5"), safe_float(row.get("Away_CornersAgainst_Last3"), 5.0))

    home_expected = (home_for * 0.60) + (away_against * 0.40)
    away_expected = (away_for * 0.60) + (home_against * 0.40)

    home_expected = max(home_expected, 1.0)
    away_expected = max(away_expected, 1.0)
    total_expected = home_expected + away_expected

    return round(home_expected, 3), round(away_expected, 3), round(total_expected, 3)


def _corner_probabilities(row: pd.Series, total_expected: float) -> tuple[float, float, float]:
    home_over95 = safe_float(row.get("Home_Over95Corners_Last5"), 0.50)
    away_over95 = safe_float(row.get("Away_Over95Corners_Last5"), 0.50)
    form_over95 = (home_over95 + away_over95) / 2

    over85_base = sigmoid(total_expected, centre=8.5, scale=1.55)
    over95_base = sigmoid(total_expected, centre=9.5, scale=1.55)
    over105_base = sigmoid(total_expected, centre=10.5, scale=1.60)

    over85 = clamp_probability((over85_base * 0.75) + (form_over95 * 0.25))
    over95 = clamp_probability((over95_base * 0.70) + (form_over95 * 0.30))
    over105 = clamp_probability((over105_base * 0.80) + (form_over95 * 0.20))

    return round(over85, 4), round(over95, 4), round(over105, 4)


def _best_corners_signal(over85: float, over95: float, over105: float) -> tuple[str, str, float]:
    candidates = [
        ("Corners", "Over 8.5 Corners", over85),
        ("Corners", "Over 9.5 Corners", over95),
        ("Corners", "Over 10.5 Corners", over105),
    ]

    best_market, best_signal, best_probability = max(candidates, key=lambda item: item[2])
    return best_market, best_signal, round(best_probability, 4)


def build_corners_predictions() -> pd.DataFrame:
    df = load_match_features()

    if df.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    generated_at = now_string()

    for _, row in df.iterrows():
        home_expected, away_expected, total_expected = _expected_corners(row)
        over85, over95, over105 = _corner_probabilities(row, total_expected)
        market, signal, probability = _best_corners_signal(over85, over95, over105)

        output = row.to_dict()
        output.update(
            {
                "ModelName": MODEL_NAME,
                "ModelVersion": MODEL_VERSION,
                "Market": market,
                "PrimaryMarketSignal": signal,
                "CornersSignal": signal,
                "HomeExpectedCorners": home_expected,
                "AwayExpectedCorners": away_expected,
                "ExpectedTotalCorners": total_expected,
                "Over85CornersProbability": over85,
                "Over95CornersProbability": over95,
                "Over105CornersProbability": over105,
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
        "CornersSignal",
        "HomeExpectedCorners",
        "AwayExpectedCorners",
        "ExpectedTotalCorners",
        "Over85CornersProbability",
        "Over95CornersProbability",
        "Over105CornersProbability",
        "ModelProbability",
        "ConfidenceScore",
        "ConfidenceLabel",
        "ElitePrediction",
        "GeneratedAt",
    ]

    columns = [col for col in preferred_columns if col in out.columns]
    extra_columns = [col for col in out.columns if col not in columns]

    return out[columns + extra_columns]


def export_corners_predictions() -> pd.DataFrame:
    predictions = build_corners_predictions()
    rows = save_model_table(CORNERS_TABLE, predictions)

    print("\nSQLite football corners model refreshed.")
    print(f"Table: {CORNERS_TABLE}")
    print(f"Rows : {rows}")

    return predictions


def main() -> None:
    print("=" * 38)
    print("SQLITE FOOTBALL CORNERS MODEL")
    print("=" * 38)
    export_corners_predictions()
    print("=" * 38)


if __name__ == "__main__":
    main()
