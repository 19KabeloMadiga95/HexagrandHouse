from __future__ import annotations

import pandas as pd

from src.data.database import (
    get_database_summary,
    read_lottery_history,
    read_lottery_predictions,
    read_football_history,
    read_football_predictions,
    read_football_ensemble_predictions,
    read_football_fixtures,
    read_football_backtest_history,
)


# ==========================================================
# PLATFORM
# ==========================================================

def get_platform_summary() -> pd.DataFrame:
    return get_database_summary()


# ==========================================================
# LOTTERY
# ==========================================================

def get_recent_lottery_results(limit: int = 20) -> pd.DataFrame:
    df = read_lottery_history()

    if df.empty:
        return df

    if "DrawDate" in df.columns:
        df = df.sort_values("DrawDate", ascending=False)

    return df.head(limit)


def get_latest_lottery_predictions(limit: int = 20) -> pd.DataFrame:
    df = read_lottery_predictions()

    if df.empty:
        return df

    if "GeneratedAt" in df.columns:
        df = df.sort_values("GeneratedAt", ascending=False)

    return df.head(limit)


# ==========================================================
# FOOTBALL
# ==========================================================

def get_recent_football_results(limit: int = 50) -> pd.DataFrame:
    df = read_football_history()

    if df.empty:
        return df

    for column in ("MatchDate", "Date"):
        if column in df.columns:
            df = df.sort_values(column, ascending=False)
            break

    return df.head(limit)


def get_upcoming_fixtures(limit: int = 50) -> pd.DataFrame:
    df = read_football_fixtures()

    if df.empty:
        return df

    for column in ("FixtureDate", "MatchDate", "Date"):
        if column in df.columns:
            df = df.sort_values(column)
            break

    return df.head(limit)


def get_latest_football_predictions(limit: int = 50) -> pd.DataFrame:
    df = read_football_predictions()

    if df.empty:
        return df

    for column in ("GeneratedAt", "CreatedAt"):
        if column in df.columns:
            df = df.sort_values(column, ascending=False)
            break

    return df.head(limit)


def get_latest_ensemble_predictions(limit: int = 50) -> pd.DataFrame:
    df = read_football_ensemble_predictions()

    if df.empty:
        return df

    for column in ("GeneratedAt", "CreatedAt", "MatchDate"):
        if column in df.columns:
            df = df.sort_values(column, ascending=False)
            break

    return df.head(limit)


def get_backtest_history(limit: int = 100) -> pd.DataFrame:
    df = read_football_backtest_history()

    if df.empty:
        return df

    for column in ("FixtureDate", "MatchDate"):
        if column in df.columns:
            df = df.sort_values(column, ascending=False)
            break

    return df.head(limit)


# ==========================================================
# SEARCH
# ==========================================================

def search_table(
    table_function,
    column: str,
    value,
) -> pd.DataFrame:
    df = table_function()

    if df.empty:
        return df

    if column not in df.columns:
        return pd.DataFrame()

    return df[df[column] == value]


# ==========================================================
# HEALTH CHECK
# ==========================================================

def health_check() -> dict:
    summary = get_platform_summary()

    return {
        "database_connected": not summary.empty,
        "tables": len(summary),
        "total_rows": int(summary["RowCount"].sum()) if not summary.empty else 0,
    }