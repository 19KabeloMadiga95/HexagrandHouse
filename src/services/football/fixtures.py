from __future__ import annotations

import pandas as pd

from src.data.query_service import get_upcoming_fixtures


def prepare_fixtures(limit: int = 500) -> pd.DataFrame:
    df = get_upcoming_fixtures(limit)

    if df.empty:
        return df

    df = df.copy()

    for col in ["FixtureDate", "FixtureDateTime", "MatchDate"]:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce",
            )

    sort_col = None

    for col in ["FixtureDateTime", "FixtureDate", "MatchDate"]:
        if col in df.columns:
            sort_col = col
            break

    if sort_col:
        df = df.sort_values(
            by=sort_col,
            ascending=True,
        )

    return df


def get_fixture_count(fixtures_df: pd.DataFrame) -> int:
    return int(len(fixtures_df))


def get_fixture_display_columns(fixtures_df: pd.DataFrame) -> list[str]:
    return [
        col for col in [
            "FixtureDate",
            "KickoffTime",
            "League",
            "Country",
            "HomeTeam",
            "AwayTeam",
            "Bet365HomeOdds",
            "Bet365DrawOdds",
            "Bet365AwayOdds",
            "AverageHomeOdds",
            "AverageDrawOdds",
            "AverageAwayOdds",
            "SourceName",
        ]
        if col in fixtures_df.columns
    ]