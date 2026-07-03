from __future__ import annotations

import pandas as pd

from src.core.formatting import clean_text


def build_game_display(row) -> str:
    game_family = clean_text(row.get("GameFamily"))
    game_name = clean_text(row.get("GameName"))
    draw_type = clean_text(row.get("DrawType"))

    base_name = game_name or game_family or "Unknown"

    if base_name.upper() == "UK49S" or game_family.upper() == "UK49S":
        if draw_type:
            return f"UK49s {draw_type}".strip()

        return "UK49s"

    return base_name.strip()


def add_game_display_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    df["GameDisplay"] = df.apply(
        build_game_display,
        axis=1,
    )

    return df