from pathlib import Path
import sqlite3

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

DB_FILE = BASE_DIR / "data" / "hexagrandhouse.db"


def database_exists():
    return DB_FILE.exists()


def get_database_path():
    return DB_FILE


def get_connection():
    if not database_exists():
        raise FileNotFoundError(
            f"Database file not found:\n{DB_FILE}\n\n"
            "Run this first:\n"
            "python -m src.database.build_hexagrandhouse_db"
        )

    return sqlite3.connect(DB_FILE)


def list_tables():
    if not database_exists():
        return []

    with get_connection() as conn:
        query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """

        tables = pd.read_sql_query(
            query,
            conn
        )

    return tables["name"].tolist()


def table_exists(table_name):
    return table_name in list_tables()


def read_table(table_name, limit=None):
    if not table_exists(table_name):
        return pd.DataFrame()

    query = f"SELECT * FROM {table_name}"

    if limit:
        query += f" LIMIT {int(limit)}"

    with get_connection() as conn:
        df = pd.read_sql_query(
            query,
            conn
        )

    return df


def run_query(query, params=None):
    if params is None:
        params = []

    with get_connection() as conn:
        df = pd.read_sql_query(
            query,
            conn,
            params=params
        )

    return df


def get_table_row_count(table_name):
    if not table_exists(table_name):
        return 0

    query = f"SELECT COUNT(*) AS row_count FROM {table_name}"

    with get_connection() as conn:
        df = pd.read_sql_query(
            query,
            conn
        )

    if df.empty:
        return 0

    return int(df.loc[0, "row_count"])


def get_database_summary():
    tables = list_tables()

    rows = []

    for table in tables:
        rows.append({
            "TableName": table,
            "RowCount": get_table_row_count(table),
        })

    return pd.DataFrame(rows)


def read_lottery_predictions():
    return read_table("lottery_predictions")


def read_lottery_history():
    return read_table("lottery_history")


def read_football_history():
    return read_table("football_history")


def read_football_predictions():
    if table_exists("football_predictions"):
        return read_table("football_predictions")

    if table_exists("football_ensemble_predictions"):
        return read_table("football_ensemble_predictions")

    return pd.DataFrame()


def read_football_ensemble_predictions():
    return read_table("football_ensemble_predictions")


def read_football_fixtures():
    return read_table("football_fixtures")


def read_football_backtest_history():
    return read_table("football_backtest_history")