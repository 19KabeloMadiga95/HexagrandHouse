from __future__ import annotations

import pandas as pd

from src.data.database import read_football_backtest_history


def load_accuracy_history() -> pd.DataFrame:
    df = read_football_backtest_history()

    if df.empty:
        return df

    df = df.copy()

    for col in ["FixtureDate", "MatchDate", "ResultDate"]:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce",
            )

    for col in ["ResultHit", "GoalsHit", "CornersHit"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

    return df