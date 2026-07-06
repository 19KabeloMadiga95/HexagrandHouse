from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Any

import pandas as pd

from src.core.paths import DATABASE_FILE, ensure_parent_directory
from src.data.database import get_connection, read_table, run_query, table_exists


# ==========================================================
# SQLITE STORAGE HELPERS
# ==========================================================


def normalise_for_sqlite(df: pd.DataFrame | None) -> pd.DataFrame:
    """
    Convert pandas values into SQLite-friendly values.

    This helper is intentionally lightweight and reusable across the
    platform. It keeps model and automation scripts from writing pandas-only
    dtypes directly into SQLite.
    """

    if df is None:
        return pd.DataFrame()

    if df.empty:
        return df.copy()

    out = df.copy()

    for column in out.columns:
        series = out[column]

        if pd.api.types.is_datetime64_any_dtype(series):
            out[column] = series.dt.strftime("%Y-%m-%d %H:%M:%S")
            out[column] = out[column].where(out[column].notna(), None)
            continue

        if isinstance(series.dtype, pd.CategoricalDtype):
            out[column] = series.astype(str).replace("nan", None)
            continue

        if pd.api.types.is_object_dtype(series):
            out[column] = series.where(series.notna(), None)

    return out


def replace_sqlite_table(
    table_name: str,
    df: pd.DataFrame | None,
    db_file: Path = DATABASE_FILE,
) -> int:
    """Replace a SQLite table with a dataframe and return the row count."""

    ensure_parent_directory(db_file)
    clean_df = normalise_for_sqlite(df)

    with get_connection(db_file) as conn:
        clean_df.to_sql(
            table_name,
            conn,
            if_exists="replace",
            index=False,
        )

    return len(clean_df)


def append_sqlite_table(
    table_name: str,
    df: pd.DataFrame | None,
    db_file: Path = DATABASE_FILE,
) -> int:
    """Append a dataframe to a SQLite table and return the appended row count."""

    ensure_parent_directory(db_file)
    clean_df = normalise_for_sqlite(df)

    if clean_df.empty:
        return 0

    with get_connection(db_file) as conn:
        clean_df.to_sql(
            table_name,
            conn,
            if_exists="append",
            index=False,
        )

    return len(clean_df)


def read_sqlite_table(
    table_name: str,
    limit: int | None = None,
) -> pd.DataFrame:
    """Read a whole SQLite table, returning an empty dataframe if missing."""

    return read_table(table_name, limit=limit, warn_if_missing=False)


def create_indexes(
    table_name: str,
    columns: Iterable[str],
    db_file: Path = DATABASE_FILE,
) -> None:
    """Create indexes for columns that exist on a table."""

    if not table_exists(table_name, db_file=db_file):
        return

    sample = read_table(table_name, db_file=db_file, limit=1, warn_if_missing=False)
    available_columns = set(sample.columns)

    if not available_columns:
        return

    with get_connection(db_file) as conn:
        for column in columns:
            if column not in available_columns:
                continue

            index_name = f"idx_{table_name}_{column}".replace(" ", "_").replace("-", "_")
            conn.execute(
                f'CREATE INDEX IF NOT EXISTS "{index_name}" '
                f'ON "{table_name}" ("{column}")'
            )


def execute_sql(
    sql: str,
    params: Iterable[Any] | Mapping[str, Any] | None = None,
    db_file: Path = DATABASE_FILE,
) -> None:
    """Execute a non-query SQL statement."""

    ensure_parent_directory(db_file)

    with get_connection(db_file) as conn:
        conn.execute(sql, params or [])
        conn.commit()


def query_sqlite(
    sql: str,
    params: Iterable[Any] | Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    """Run an ad-hoc SQLite query and return a dataframe."""

    return run_query(sql, params=params)


def get_latest_row(
    table_name: str,
    order_column: str,
) -> pd.DataFrame:
    """Return the latest row from a table, or an empty dataframe."""

    if not table_exists(table_name):
        return pd.DataFrame()

    sample = read_sqlite_table(table_name, limit=1)
    if order_column not in sample.columns:
        return pd.DataFrame()

    return query_sqlite(
        f'SELECT * FROM "{table_name}" ORDER BY "{order_column}" DESC LIMIT 1'
    )
