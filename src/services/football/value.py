from __future__ import annotations

import pandas as pd


def prepare_value_bets(predictions_df: pd.DataFrame) -> pd.DataFrame:
    if predictions_df.empty:
        return predictions_df

    df = predictions_df.copy()

    if "ValueScore" in df.columns:
        df["ValueScore"] = pd.to_numeric(
            df["ValueScore"],
            errors="coerce",
        ).fillna(0)

        df = df.sort_values(
            by="ValueScore",
            ascending=False,
        )

    return df


def get_value_display_columns(df: pd.DataFrame) -> list[str]:
    return [
        col for col in [
            "League",
            "HomeTeam",
            "AwayTeam",
            "Market",
            "PredictedResult",
            "ModelProbability",
            "BookmakerOdds",
            "ValueEdgePercent",
            "ValueRating",
            "ValueScore",
            "ConfidenceScore",
            "ConfidenceLabel",
        ]
        if col in df.columns
    ]