from __future__ import annotations

import pandas as pd

from src.core.paths import (
    DATABASE_FILE,
    LOTTERY_MASTER_FILE,
    LOTTERY_ALL_GAMES_PREDICTIONS_FILE,
    FOOTBALL_HISTORY_FILE,
    FOOTBALL_FIXTURE_PREDICTIONS_FILE,
    FOOTBALL_ENSEMBLE_PREDICTIONS_FILE,
    FOOTBALL_BACKTEST_HISTORY_FILE,
    FOOTBALL_FIXTURES_FILE,
    ensure_parent_directory,
)
from src.core.excel import read_excel_preferred
from src.core.sqlite import get_connection, write_dataframe, create_indexes
from src.core.logging import (
    pipeline_banner,
    pipeline_complete,
    info,
)


INDEX_SPECS = [
    {"index_name": "idx_lottery_history_game", "table_name": "lottery_history", "column_name": "GameName"},
    {"index_name": "idx_lottery_history_date", "table_name": "lottery_history", "column_name": "DrawDate"},
    {"index_name": "idx_lottery_predictions_game", "table_name": "lottery_predictions", "column_name": "GameName"},
    {"index_name": "idx_lottery_predictions_generated", "table_name": "lottery_predictions", "column_name": "GeneratedAt"},

    {"index_name": "idx_football_history_date", "table_name": "football_history", "column_name": "MatchDate"},
    {"index_name": "idx_football_history_league", "table_name": "football_history", "column_name": "League"},

    {"index_name": "idx_football_predictions_date", "table_name": "football_predictions", "column_name": "FixtureDate"},
    {"index_name": "idx_football_predictions_league", "table_name": "football_predictions", "column_name": "League"},

    {"index_name": "idx_football_ensemble_date", "table_name": "football_ensemble_predictions", "column_name": "MatchDate"},
    {"index_name": "idx_football_ensemble_league", "table_name": "football_ensemble_predictions", "column_name": "League"},

    {"index_name": "idx_football_backtest_date", "table_name": "football_backtest_history", "column_name": "FixtureDate"},

    {"index_name": "idx_football_fixtures_date", "table_name": "football_fixtures", "column_name": "FixtureDate"},
    {"index_name": "idx_football_fixtures_league", "table_name": "football_fixtures", "column_name": "League"},
]


OPTIONAL_TABLES = {
    "football_predictions",
    "football_backtest_history",
}


def prepare_football_fixtures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Database builder should not decide fixture eligibility.
    It only standardises columns and loads what the fixture builder exported.
    """
    if df.empty:
        return df

    df = df.copy()

    rename_map = {
        "Date": "FixtureDate",
        "Time": "KickoffTime",
        "Home": "HomeTeam",
        "Away": "AwayTeam",
        "Home_Team": "HomeTeam",
        "Away_Team": "AwayTeam",
    }

    df = df.rename(
        columns={
            old: new
            for old, new in rename_map.items()
            if old in df.columns
        }
    )

    if "FixtureDate" in df.columns:
        df["FixtureDate"] = pd.to_datetime(
            df["FixtureDate"],
            errors="coerce",
        )

    if "FixtureDateTime" in df.columns:
        df["FixtureDateTime"] = pd.to_datetime(
            df["FixtureDateTime"],
            errors="coerce",
        )

    if "KickoffTime" in df.columns:
        df["KickoffTime"] = df["KickoffTime"].astype(str)

    df["LoadedAt"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    return df


def load_lottery_history() -> pd.DataFrame:
    return read_excel_preferred(
        LOTTERY_MASTER_FILE,
        ["Historical_Results", "Lottery_History", "Sheet1"],
    )


def load_football_history() -> pd.DataFrame:
    return read_excel_preferred(
        FOOTBALL_HISTORY_FILE,
        ["Football_Master", "Master", "Sheet1"],
    )


def load_lottery_predictions() -> pd.DataFrame:
    return read_excel_preferred(
        LOTTERY_ALL_GAMES_PREDICTIONS_FILE,
        [
            "All_Predictions",
            "Final_Predictions",
            "All_Ensemble_Predictions",
            "Sheet1",
        ],
    )


def load_football_predictions() -> pd.DataFrame:
    return read_excel_preferred(
        FOOTBALL_FIXTURE_PREDICTIONS_FILE,
        [
            "Fixture_Predictions",
            "Football_Predictions",
            "Predictions",
            "Sheet1",
        ],
    )


def load_football_ensemble_predictions() -> pd.DataFrame:
    return read_excel_preferred(
        FOOTBALL_ENSEMBLE_PREDICTIONS_FILE,
        [
            "Ensemble_Predictions",
            "All_Ensemble_Predictions",
            "Elite_Predictions",
            "Sheet1",
        ],
    )


def load_football_backtest_history() -> pd.DataFrame:
    return read_excel_preferred(
        FOOTBALL_BACKTEST_HISTORY_FILE,
        [
            "Backtest_History",
            "History",
            "Sheet1",
        ],
        warn_if_missing=False,
    )


def load_football_fixtures() -> pd.DataFrame:
    df = read_excel_preferred(
        FOOTBALL_FIXTURES_FILE,
        ["Football_Fixtures", "Fixtures", "Sheet1"],
    )

    return prepare_football_fixtures(df)


def build_database() -> str:
    pipeline_banner("Build HexagrandHouse Database")

    ensure_parent_directory(DATABASE_FILE)

    datasets = [
        ("lottery_history", load_lottery_history()),
        ("football_history", load_football_history()),
        ("lottery_predictions", load_lottery_predictions()),
        ("football_predictions", load_football_predictions()),
        ("football_ensemble_predictions", load_football_ensemble_predictions()),
        ("football_backtest_history", load_football_backtest_history()),
        ("football_fixtures", load_football_fixtures()),
    ]

    with get_connection(DATABASE_FILE) as conn:
        for table_name, df in datasets:
            write_dataframe(
                conn=conn,
                df=df,
                table_name=table_name,
                if_exists="replace",
                warn_if_empty=table_name not in OPTIONAL_TABLES,
            )

        create_indexes(conn, INDEX_SPECS)

    info(f"Database built: {DATABASE_FILE}")

    pipeline_complete("Build HexagrandHouse Database")

    return str(DATABASE_FILE)


def build_hexagrandhouse_db() -> str:
    return build_database()


def main():
    build_database()


if __name__ == "__main__":
    main()