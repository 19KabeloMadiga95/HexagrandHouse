from __future__ import annotations

import pandas as pd

from src.core.constants import get_confidence_label
from src.data.query_service import (
    get_latest_football_predictions,
    get_latest_ensemble_predictions,
)


def prepare_football_predictions(limit: int = 500) -> pd.DataFrame:
    df = get_latest_football_predictions(limit)

    if df.empty:
        df = get_latest_ensemble_predictions(limit)

    if df.empty:
        return df

    df = df.copy()

    for col in ["FixtureDate", "FixtureDateTime", "MatchDate", "GeneratedAt"]:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce",
            )

    confidence_cols = [
        "EnsembleConfidenceScore",
        "ConfidenceScore",
        "ModelProbability",
        "PredictedResultProbability",
        "ValueScore",
    ]

    confidence_col = None

    for col in confidence_cols:
        if col in df.columns:
            confidence_col = col
            break

    if confidence_col:
        df[confidence_col] = pd.to_numeric(
            df[confidence_col],
            errors="coerce",
        )

        df["ConfidenceScore"] = df[confidence_col].fillna(0).round(2)
        df["ConfidenceLabel"] = df["ConfidenceScore"].apply(
            get_confidence_label
        )
    else:
        df["ConfidenceScore"] = 0
        df["ConfidenceLabel"] = "Unrated"

    return df


def get_top_predictions(
    predictions_df: pd.DataFrame,
    limit: int = 12,
) -> pd.DataFrame:
    if predictions_df.empty:
        return predictions_df

    df = predictions_df.copy()

    sort_cols = [
        "ElitePrediction",
        "ConfidenceScore",
        "EnsembleConfidenceScore",
        "ValueScore",
    ]

    available = [
        col for col in sort_cols
        if col in df.columns
    ]

    for col in available:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        ).fillna(0)

    if available:
        df = df.sort_values(
            by=available,
            ascending=[False] * len(available),
        )

    return df.head(limit)