from __future__ import annotations

import pandas as pd


def get_league_count(*dataframes: pd.DataFrame) -> int:
    leagues = set()

    for df in dataframes:
        if df is None or df.empty:
            continue

        if "League" in df.columns:
            leagues.update(
                df["League"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

    return len(leagues)


def get_average_confidence(predictions_df: pd.DataFrame):
    if predictions_df.empty:
        return "-"

    for col in ["ConfidenceScore", "EnsembleConfidenceScore"]:
        if col in predictions_df.columns:
            value = pd.to_numeric(
                predictions_df[col],
                errors="coerce",
            ).mean()

            if pd.notna(value):
                return round(float(value), 2)

    return "-"


def get_league_fixture_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "League" not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby("League")
        .size()
        .reset_index(name="FixtureCount")
        .sort_values("FixtureCount", ascending=False)
    )


def get_elite_prediction_count(predictions_df: pd.DataFrame) -> int:
    if predictions_df.empty:
        return 0

    if "ElitePrediction" not in predictions_df.columns:
        return 0

    return int(
        pd.to_numeric(
            predictions_df["ElitePrediction"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
        .sum()
    )