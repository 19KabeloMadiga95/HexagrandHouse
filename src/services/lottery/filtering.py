from __future__ import annotations

import pandas as pd

from src.services.lottery.display import add_game_display_column


def get_game_options(*dataframes: pd.DataFrame) -> list[str]:
    games = set()

    for df in dataframes:
        if df is None or df.empty:
            continue

        temp = add_game_display_column(df)

        if "GameDisplay" in temp.columns:
            games.update(
                temp["GameDisplay"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

    return ["All"] + sorted(games)


def filter_by_game(
    df: pd.DataFrame,
    selected_game: str,
) -> pd.DataFrame:
    if df.empty:
        return df

    if selected_game == "All":
        return df

    temp = add_game_display_column(df)

    if "GameDisplay" not in temp.columns:
        return temp

    return temp[
        temp["GameDisplay"].astype(str) == selected_game
    ].copy()