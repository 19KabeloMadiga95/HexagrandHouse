from pathlib import Path
import sqlite3
import pandas as pd

from src.core.paths import DATABASE_FILE, ensure_parent_directory
from src.core.excel import clean_column_names, normalise_date_columns
from src.core.logging import info, warning


def get_connection(db_file: Path = DATABASE_FILE):
    ensure_parent_directory(db_file)
    return sqlite3.connect(db_file)


def table_exists_in_connection(conn, table_name: str) -> bool:
    result = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name=?
        """,
        (table_name,),
    ).fetchone()

    return result is not None


def column_exists_in_connection(conn, table_name: str, column_name: str) -> bool:
    if not table_exists_in_connection(conn, table_name):
        return False

    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(row[1] == column_name for row in columns)


def write_dataframe(
    conn,
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "replace",
    warn_if_empty: bool = True,
) -> bool:
    df = clean_column_names(df)
    df = normalise_date_columns(df)

    if df.empty:
        if len(df.columns) > 0:
            df.to_sql(
                table_name,
                conn,
                if_exists=if_exists,
                index=False,
            )
            info(f"Loaded empty table: {table_name} | Rows: 0")
            return True

        if warn_if_empty:
            warning(f"Skipped empty table: {table_name}")

        return False

    df.to_sql(
        table_name,
        conn,
        if_exists=if_exists,
        index=False,
    )

    info(f"Loaded table: {table_name} | Rows: {len(df)}")
    return True

def read_table(
    table_name: str,
    db_file: Path = DATABASE_FILE,
) -> pd.DataFrame:
    try:
        with get_connection(db_file) as conn:
            return pd.read_sql_query(
                f"SELECT * FROM {table_name}",
                conn,
            )
    except Exception as exc:
        warning(f"Could not read table {table_name}: {exc}")
        return pd.DataFrame()


def run_query(
    query: str,
    params: list | tuple | None = None,
    db_file: Path = DATABASE_FILE,
) -> pd.DataFrame:
    try:
        with get_connection(db_file) as conn:
            return pd.read_sql_query(
                query,
                conn,
                params=params,
            )
    except Exception as exc:
        warning(f"Query failed: {exc}")
        return pd.DataFrame()


def table_exists(
    table_name: str,
    db_file: Path = DATABASE_FILE,
) -> bool:
    query = """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
      AND name=?
    """

    df = run_query(query, [table_name], db_file)
    return not df.empty


def create_indexes(conn, index_specs: list[dict]):
    for spec in index_specs:
        index_name = spec["index_name"]
        table_name = spec["table_name"]
        column_name = spec["column_name"]

        if not column_exists_in_connection(
            conn,
            table_name,
            column_name,
        ):
            continue

        sql = (
            f"CREATE INDEX IF NOT EXISTS {index_name} "
            f"ON {table_name}({column_name});"
        )

        conn.execute(sql)

    conn.commit()