from __future__ import annotations

import pandas as pd


def get_lottery_game_options(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["All"]

    col = "GameDisplay" if "GameDisplay" in df.columns else "GameName"

    if col not in df.columns:
        return ["All"]

    return ["All"] + sorted(
        df[col]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


def get_football_league_options(df: pd.DataFrame) -> list[str]:
    if df.empty or "League" not in df.columns:
        return ["All"]

    return ["All"] + sorted(
        df["League"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


def filter_lottery_game(
    df: pd.DataFrame,
    selected_game: str,
) -> pd.DataFrame:
    if df.empty or selected_game == "All":
        return df

    col = "GameDisplay" if "GameDisplay" in df.columns else "GameName"

    if col not in df.columns:
        return df

    return df[df[col].astype(str) == selected_game].copy()


def filter_football_league(
    df: pd.DataFrame,
    selected_league: str,
) -> pd.DataFrame:
    if df.empty or selected_league == "All":
        return df

    if "League" not in df.columns:
        return df

    return df[df["League"].astype(str) == selected_league].copy()