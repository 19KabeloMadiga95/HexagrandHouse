from __future__ import annotations

import pandas as pd

from src.core.constants import get_confidence_label
from src.data.query_service import get_latest_lottery_predictions
from src.services.lottery.display import add_game_display_column


CONFIDENCE_COLUMNS = [
    "ConfidenceScore",
    "EnsembleConfidenceScore",
    "Confidence",
    "EnsembleScore",
    "RawScore",
    "FitnessScore",
    "Score",
    "PredictionScore",
]


def prepare_lottery_predictions(limit: int = 300) -> pd.DataFrame:
    df = get_latest_lottery_predictions(limit)

    if df.empty:
        return df

    df = add_game_display_column(df)

    if "GeneratedAt" in df.columns:
        df["GeneratedAt"] = pd.to_datetime(
            df["GeneratedAt"],
            errors="coerce",
        )

        df = df.sort_values(
            by="GeneratedAt",
            ascending=False,
        )

    confidence_col = None

    for col in CONFIDENCE_COLUMNS:
        if col in df.columns:
            confidence_col = col
            break

    if confidence_col is None:
        df["ConfidenceScore"] = 0
        df["ConfidenceLabel"] = "Unrated"
        return df

    scores = pd.to_numeric(
        df[confidence_col],
        errors="coerce",
    )

    if confidence_col in {"RawScore", "FitnessScore", "EnsembleScore"}:
        min_score = scores.min()
        max_score = scores.max()

        if pd.notna(min_score) and pd.notna(max_score) and max_score > min_score:
            scores = ((scores - min_score) / (max_score - min_score)) * 100
        else:
            scores = 0

    df["ConfidenceScore"] = pd.Series(scores).fillna(0).round(1)
    df["ConfidenceLabel"] = df["ConfidenceScore"].apply(get_confidence_label)

    return df


def get_prediction_display_columns(df: pd.DataFrame) -> list[str]:
    return [
        col for col in [
            "GameDisplay",
            "GameFamily",
            "GameName",
            "DrawType",
            "PredictionRank",
            "Rank",
            "N1",
            "N2",
            "N3",
            "N4",
            "N5",
            "N6",
            "Bonus",
            "RegularSum",
            "HighCount",
            "LowCount",
            "OddCount",
            "EvenCount",
            "ConfidenceScore",
            "ConfidenceLabel",
            "ModelName",
            "ModelVersion",
            "GeneratedAt",
        ]
        if col in df.columns
    ]