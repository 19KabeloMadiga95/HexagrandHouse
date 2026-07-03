from __future__ import annotations

import pandas as pd

from src.data.query_service import get_recent_lottery_results
from src.services.lottery.display import add_game_display_column


def prepare_lottery_results(limit: int = 300) -> pd.DataFrame:
    df = get_recent_lottery_results(limit)

    if df.empty:
        return df

    df = add_game_display_column(df)

    if "DrawDate" in df.columns:
        df["DrawDate"] = pd.to_datetime(
            df["DrawDate"],
            errors="coerce",
        )

        df = df.sort_values(
            by="DrawDate",
            ascending=False,
        )

    return df


def get_latest_results(
    results_df: pd.DataFrame,
    limit: int = 12,
) -> pd.DataFrame:
    if results_df.empty:
        return results_df

    df = results_df.copy()

    if "DrawDate" in df.columns:
        df["DrawDate"] = pd.to_datetime(
            df["DrawDate"],
            errors="coerce",
        )

        df = df.sort_values(
            by="DrawDate",
            ascending=False,
        )

    return df.head(limit)


def get_results_display_columns(df: pd.DataFrame) -> list[str]:
    return [
        col for col in [
            "GameDisplay",
            "GameFamily",
            "GameName",
            "DrawType",
            "DrawDate",
            "N1",
            "N2",
            "N3",
            "N4",
            "N5",
            "N6",
            "Bonus",
        ]
        if col in df.columns
    ]