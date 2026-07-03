from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd

from src.core.paths import DATABASE_FILE, ensure_parent_directory
from src.core.constants import DATABASE_TABLES
from src.core.logging import warning


def get_database_path() -> Path:
    return DATABASE_FILE


def database_exists() -> bool:
    return DATABASE_FILE.exists()


def get_connection(db_file: Path = DATABASE_FILE):
    ensure_parent_directory(db_file)
    return sqlite3.connect(db_file)


def run_query(
    query: str,
    params: list | tuple | None = None,
    db_file: Path = DATABASE_FILE,
) -> pd.DataFrame:
    try:
        with get_connection(db_file) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as exc:
        warning(f"Query failed: {exc}")
        return pd.DataFrame()


def list_tables(db_file: Path = DATABASE_FILE) -> list[str]:
    df = run_query(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
        """,
        db_file=db_file,
    )

    if df.empty or "name" not in df.columns:
        return []

    return df["name"].tolist()


def table_exists(table_name: str, db_file: Path = DATABASE_FILE) -> bool:
    df = run_query(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name=?
        """,
        params=[table_name],
        db_file=db_file,
    )

    return not df.empty


def read_table(
    table_name: str,
    db_file: Path = DATABASE_FILE,
    limit: int | None = None,
    warn_if_missing: bool = True,
) -> pd.DataFrame:
    if not table_exists(table_name, db_file):
        if warn_if_missing:
            warning(f"Table does not exist: {table_name}")
        return pd.DataFrame()

    query = f"SELECT * FROM {table_name}"

    if limit is not None:
        query += f" LIMIT {int(limit)}"

    return run_query(query, db_file=db_file)


def get_table_row_count(
    table_name: str,
    db_file: Path = DATABASE_FILE,
) -> int:
    if not table_exists(table_name, db_file):
        return 0

    df = run_query(
        f"SELECT COUNT(*) AS RowCount FROM {table_name}",
        db_file=db_file,
    )

    if df.empty:
        return 0

    return int(df.iloc[0]["RowCount"])


def get_database_summary(db_file: Path = DATABASE_FILE) -> pd.DataFrame:
    rows = []

    for table_name in list_tables(db_file):
        rows.append(
            {
                "TableName": table_name,
                "RowCount": get_table_row_count(table_name, db_file),
            }
        )

    return pd.DataFrame(rows)


def read_lottery_history(limit: int | None = None) -> pd.DataFrame:
    return read_table(DATABASE_TABLES["lottery_history"], limit=limit)


def read_lottery_predictions(limit: int | None = None) -> pd.DataFrame:
    return read_table(DATABASE_TABLES["lottery_predictions"], limit=limit)


def read_football_history(limit: int | None = None) -> pd.DataFrame:
    return read_table(DATABASE_TABLES["football_history"], limit=limit)


def read_football_fixtures(limit: int | None = None) -> pd.DataFrame:
    return read_table(DATABASE_TABLES["football_fixtures"], limit=limit)


def read_football_predictions(limit: int | None = None) -> pd.DataFrame:
    return read_table(
        DATABASE_TABLES["football_predictions"],
        limit=limit,
        warn_if_missing=False,
    )


def read_football_ensemble_predictions(limit: int | None = None) -> pd.DataFrame:
    return read_table(
        DATABASE_TABLES["football_ensemble_predictions"],
        limit=limit,
    )


def read_football_backtest_history(limit: int | None = None) -> pd.DataFrame:
    return read_table(
        DATABASE_TABLES["football_backtest_history"],
        limit=limit,
        warn_if_missing=False,
    )