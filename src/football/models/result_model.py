from __future__ import annotations

import pandas as pd

from src.football.models.sqlite_football_model_engine import (
    RESULT_TABLE,
    base_output_columns,
    clamp_probability,
    confidence_label,
    load_match_features,
    normalize_three_way,
    now_string,
    safe_float,
    save_model_table,
    sigmoid,
)


# =========================================================
# RESULT MODEL
# =========================================================

MODEL_NAME = "SQLite Result Signal Model"
MODEL_VERSION = "football_result_sqlite_v1"


def _result_probabilities(row: pd.Series) -> tuple[float, float, float]:
    form_diff = safe_float(row.get("FormPointsDiff_Last5"), safe_float(row.get("FormPointsDiff_Last3"), 0.0))
    attack_diff = safe_float(row.get("AttackStrengthDiff_Last5"), safe_float(row.get("AttackStrengthDiff_Last3"), 0.0))
    defence_diff = safe_float(row.get("DefenceWeaknessDiff_Last5"), safe_float(row.get("DefenceWeaknessDiff_Last3"), 0.0))

    # Positive score favours the home team. A small home edge is included
    # because football historically has home advantage.
    rating_score = (
        0.36
        + (form_diff * 0.18)
        + (attack_diff * 0.30)
        - (defence_diff * 0.20)
    )

    home_raw = sigmoid(rating_score, centre=0.15, scale=0.95)
    away_raw = sigmoid(-rating_score, centre=0.15, scale=0.95)

    # Draw probability is highest where teams look balanced and lower where
    # the model sees a clear edge.
    balance = max(0.0, 1 - abs(rating_score) / 2.4)
    draw_raw = 0.45 * balance + 0.12

    home_prob, draw_prob, away_prob = normalize_three_way(
        home_raw,
        draw_raw,
        away_raw,
    )

    return home_prob, draw_prob, away_prob


def _best_result_pick(home_prob: float, draw_prob: float, away_prob: float) -> tuple[str, str, float]:
    candidates = [
        ("H", "Home Win", home_prob),
        ("D", "Draw", draw_prob),
        ("A", "Away Win", away_prob),
    ]

    code, label, probability = max(candidates, key=lambda item: item[2])
    return code, label, round(probability, 4)


def build_result_predictions() -> pd.DataFrame:
    df = load_match_features()

    if df.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    generated_at = now_string()

    for _, row in df.iterrows():
        home_prob, draw_prob, away_prob = _result_probabilities(row)
        code, label, probability = _best_result_pick(home_prob, draw_prob, away_prob)

        output = row.to_dict()
        output.update(
            {
                "ModelName": MODEL_NAME,
                "ModelVersion": MODEL_VERSION,
                "Market": "Result",
                "PrimaryMarketSignal": label,
                "PredictedResult": code,
                "PredictedResultLabel": label,
                "HomeWinProbability": home_prob,
                "DrawProbability": draw_prob,
                "AwayWinProbability": away_prob,
                "PredictedResultProbability": probability,
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
        "PredictedResult",
        "PredictedResultLabel",
        "HomeWinProbability",
        "DrawProbability",
        "AwayWinProbability",
        "PredictedResultProbability",
        "ModelProbability",
        "ConfidenceScore",
        "ConfidenceLabel",
        "ElitePrediction",
        "GeneratedAt",
    ]

    columns = [col for col in preferred_columns if col in out.columns]
    extra_columns = [col for col in out.columns if col not in columns]

    return out[columns + extra_columns]


def export_result_predictions() -> pd.DataFrame:
    predictions = build_result_predictions()
    rows = save_model_table(RESULT_TABLE, predictions)

    print("\nSQLite football result model refreshed.")
    print(f"Table: {RESULT_TABLE}")
    print(f"Rows : {rows}")

    return predictions


def main() -> None:
    print("=" * 38)
    print("SQLITE FOOTBALL RESULT MODEL")
    print("=" * 38)
    export_result_predictions()
    print("=" * 38)


if __name__ == "__main__":
    main()
