from pathlib import Path
import sqlite3

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_FILE = BASE_DIR / "data" / "hexagrandhouse.db"

LOTTERY_HISTORY_FILE = (
    BASE_DIR / "data" / "master" / "lottery_historical_master.xlsx"
)

FOOTBALL_HISTORY_FILE = (
    BASE_DIR / "data" / "football" / "master" / "football_master_all_leagues.xlsx"
)

LOTTERY_PREDICTIONS_FILE = (
    BASE_DIR / "data" / "exports" / "final_predictions" / "all_games_ensemble_predictions.xlsx"
)

FOOTBALL_PREDICTIONS_FILE = (
    BASE_DIR / "data" / "football" / "exports" / "predictions" / "football_fixture_predictions.xlsx"
)

FOOTBALL_ENSEMBLE_FILE = (
    BASE_DIR / "data" / "football" / "exports" / "predictions" / "football_ensemble_predictions.xlsx"
)

FOOTBALL_BACKTEST_FILE = (
    BASE_DIR / "data" / "football" / "exports" / "backtesting" / "football_fixture_backtest_history.xlsx"
)

FOOTBALL_FIXTURES_FILE = (
    BASE_DIR / "data" / "football" / "master" / "football_fixtures.xlsx"
)


# =========================================================
# HELPERS
# =========================================================

def ensure_database_folder():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)


def list_excel_sheets(path):
    try:
        if not path.exists():
            return []

        excel_file = pd.ExcelFile(path, engine="openpyxl")

        return excel_file.sheet_names

    except Exception:
        return []


def safe_read_excel_preferred(path, preferred_sheets):
    try:
        if not path.exists():
            print(f"Missing file: {path}")
            return pd.DataFrame()

        available_sheets = list_excel_sheets(path)

        if not available_sheets:
            print(f"No readable sheets found: {path}")
            return pd.DataFrame()

        for sheet in preferred_sheets:
            if sheet in available_sheets:
                return pd.read_excel(path, sheet_name=sheet, engine="openpyxl")

        fallback_sheet = available_sheets[0]

        print(
            f"Preferred sheets {preferred_sheets} not found in {path.name}. "
            f"Using '{fallback_sheet}' instead."
        )

        return pd.read_excel(path, sheet_name=fallback_sheet, engine="openpyxl")

    except Exception as e:
        print(f"Could not read: {path}")
        print(f"Error: {e}")
        return pd.DataFrame()


def clean_column_names(df):
    df = df.copy()

    cleaned_columns = []

    for col in df.columns:
        clean_col = (
            str(col)
            .strip()
            .replace(" ", "_")
            .replace("-", "_")
            .replace("/", "_")
            .replace("(", "")
            .replace(")", "")
            .replace(".", "_")
            .replace("%", "Pct")
        )

        cleaned_columns.append(clean_col)

    df.columns = cleaned_columns

    return df


def normalise_dates(df):
    df = df.copy()

    for col in df.columns:
        col_lower = col.lower()

        if (
            "date" in col_lower
            or "generatedat" in col_lower
            or "backtestedat" in col_lower
            or "updatedat" in col_lower
            or "loadedat" in col_lower
        ):
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce").astype(str)
            except Exception:
                pass

    return df


def write_table(conn, df, table_name):
    if df.empty:
        print(f"Skipped empty table: {table_name}")
        return

    df = clean_column_names(df)
    df = normalise_dates(df)

    df.to_sql(
        table_name,
        conn,
        if_exists="replace",
        index=False
    )

    print(f"Loaded table: {table_name} | Rows: {len(df)}")


def create_indexes(conn):
    index_sql = [
        "CREATE INDEX IF NOT EXISTS idx_lottery_history_game ON lottery_history(GameName);",
        "CREATE INDEX IF NOT EXISTS idx_lottery_history_date ON lottery_history(DrawDate);",
        "CREATE INDEX IF NOT EXISTS idx_lottery_predictions_game ON lottery_predictions(GameName);",
        "CREATE INDEX IF NOT EXISTS idx_lottery_predictions_generated ON lottery_predictions(GeneratedAt);",
        "CREATE INDEX IF NOT EXISTS idx_football_history_date ON football_history(MatchDate);",
        "CREATE INDEX IF NOT EXISTS idx_football_history_league ON football_history(League);",
        "CREATE INDEX IF NOT EXISTS idx_football_predictions_date ON football_predictions(FixtureDate);",
        "CREATE INDEX IF NOT EXISTS idx_football_predictions_league ON football_predictions(League);",
        "CREATE INDEX IF NOT EXISTS idx_football_ensemble_date ON football_ensemble_predictions(MatchDate);",
        "CREATE INDEX IF NOT EXISTS idx_football_ensemble_league ON football_ensemble_predictions(League);",
        "CREATE INDEX IF NOT EXISTS idx_football_backtest_date ON football_backtest_history(FixtureDate);",
        "CREATE INDEX IF NOT EXISTS idx_football_fixtures_date ON football_fixtures(FixtureDate);",
        "CREATE INDEX IF NOT EXISTS idx_football_fixtures_league ON football_fixtures(League);",
    ]

    for sql in index_sql:
        try:
            conn.execute(sql)
        except Exception:
            pass

    conn.commit()


# =========================================================
# TRANSFORMS
# =========================================================

def prepare_football_fixtures(df):
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
        "HomeTeam": "HomeTeam",
        "AwayTeam": "AwayTeam",
    }

    existing_rename_map = {
        old_col: new_col
        for old_col, new_col in rename_map.items()
        if old_col in df.columns
    }

    df = df.rename(columns=existing_rename_map)

    if "FixtureDate" in df.columns:
        df["FixtureDate"] = pd.to_datetime(
            df["FixtureDate"],
            errors="coerce"
        )

    if "KickoffTime" in df.columns:
        df["KickoffTime"] = df["KickoffTime"].astype(str)

    if "FixtureDate" in df.columns:
        df = df.dropna(subset=["FixtureDate"])

    # Keep future/current fixtures only where possible.
    if "FixtureDate" in df.columns:
        today = pd.Timestamp.today().normalize()

        df = df[
            df["FixtureDate"] >= today
        ].copy()

    df["LoadedAt"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    return df


# =========================================================
# LOADERS
# =========================================================

def load_lottery_history():
    return safe_read_excel_preferred(
        LOTTERY_HISTORY_FILE,
        [
            "Historical_Results",
            "Lottery_History",
            "Sheet1",
        ]
    )


def load_football_history():
    return safe_read_excel_preferred(
        FOOTBALL_HISTORY_FILE,
        [
            "Football_Master",
            "Master",
            "Sheet1",
        ]
    )


def load_lottery_predictions():
    return safe_read_excel_preferred(
        LOTTERY_PREDICTIONS_FILE,
        [
            "All_Predictions",
            "Final_Predictions",
            "Sheet1",
        ]
    )


def load_football_predictions():
    return safe_read_excel_preferred(
        FOOTBALL_PREDICTIONS_FILE,
        [
            "Fixture_Predictions",
            "Football_Predictions",
            "Predictions",
            "Sheet1",
        ]
    )


def load_football_ensemble_predictions():
    return safe_read_excel_preferred(
        FOOTBALL_ENSEMBLE_FILE,
        [
            "Ensemble_Predictions",
            "Elite_Predictions",
            "Sheet1",
        ]
    )


def load_football_backtest_history():
    return safe_read_excel_preferred(
        FOOTBALL_BACKTEST_FILE,
        [
            "Backtest_History",
            "History",
            "Sheet1",
        ]
    )


def load_football_fixtures():
    fixtures_df = safe_read_excel_preferred(
        FOOTBALL_FIXTURES_FILE,
        [
            "Football_Fixtures",
            "Fixtures",
            "Sheet1",
        ]
    )

    return prepare_football_fixtures(fixtures_df)


# =========================================================
# DATABASE BUILD
# =========================================================

def build_hexagrandhouse_db():
    ensure_database_folder()

    lottery_history = load_lottery_history()
    football_history = load_football_history()
    lottery_predictions = load_lottery_predictions()
    football_predictions = load_football_predictions()
    football_ensemble_predictions = load_football_ensemble_predictions()
    football_backtest_history = load_football_backtest_history()
    football_fixtures = load_football_fixtures()

    with sqlite3.connect(DB_FILE) as conn:
        write_table(conn, lottery_history, "lottery_history")
        write_table(conn, football_history, "football_history")
        write_table(conn, lottery_predictions, "lottery_predictions")
        write_table(conn, football_predictions, "football_predictions")
        write_table(conn, football_ensemble_predictions, "football_ensemble_predictions")
        write_table(conn, football_backtest_history, "football_backtest_history")
        write_table(conn, football_fixtures, "football_fixtures")

        create_indexes(conn)

    print("\n======================================")
    print("HEXAGRANDHOUSE DATABASE BUILT")
    print("======================================")
    print(f"File: {DB_FILE}")
    print("======================================\n")

    return DB_FILE


# =========================================================
# CLI
# =========================================================

def main():
    build_hexagrandhouse_db()


if __name__ == "__main__":
    main()