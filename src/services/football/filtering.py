from __future__ import annotations

import pandas as pd


def get_league_options(*dataframes: pd.DataFrame) -> list[str]:
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

    return ["All"] + sorted(leagues)


def filter_by_league(
    df: pd.DataFrame,
    selected_league: str,
) -> pd.DataFrame:
    if df.empty:
        return df

    if selected_league == "All":
        return df

    if "League" not in df.columns:
        return df

    return df[
        df["League"].astype(str) == selected_league
    ].copy()


def filter_elite_only(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "ElitePrediction" not in df.columns:
        return df

    return df[
        pd.to_numeric(
            df["ElitePrediction"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int) == 1
    ].copy()