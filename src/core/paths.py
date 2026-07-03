from pathlib import Path


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"


# =========================================================
# DATA ROOTS
# =========================================================

DATA_DIR = PROJECT_ROOT / "data"

LOTTERY_DATA_DIR = DATA_DIR / "lottery"
FOOTBALL_DATA_DIR = DATA_DIR / "football"

MASTER_DATA_DIR = DATA_DIR / "master"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = DATA_DIR / "logs"


# =========================================================
# DATABASE
# =========================================================

DATABASE_FILE = DATA_DIR / "hexagrandhouse.db"


# =========================================================
# LOTTERY PATHS
# =========================================================

LOTTERY_MASTER_FILE = MASTER_DATA_DIR / "lottery_historical_master.xlsx"

LOTTERY_FINAL_PREDICTIONS_DIR = (
    EXPORTS_DIR / "final_predictions"
)

LOTTERY_ALL_GAMES_PREDICTIONS_FILE = (
    LOTTERY_FINAL_PREDICTIONS_DIR / "all_games_ensemble_predictions.xlsx"
)

LOTTO_ENSEMBLE_PREDICTIONS_FILE = (
    LOTTERY_FINAL_PREDICTIONS_DIR / "lotto_ensemble_predictions.xlsx"
)

POWERBALL_ENSEMBLE_PREDICTIONS_FILE = (
    LOTTERY_FINAL_PREDICTIONS_DIR / "powerball_ensemble_predictions.xlsx"
)

UK49S_LUNCHTIME_ENSEMBLE_PREDICTIONS_FILE = (
    LOTTERY_FINAL_PREDICTIONS_DIR / "uk49s_lunchtime_ensemble_predictions.xlsx"
)

UK49S_TEATIME_ENSEMBLE_PREDICTIONS_FILE = (
    LOTTERY_FINAL_PREDICTIONS_DIR / "uk49s_teatime_ensemble_predictions.xlsx"
)


# =========================================================
# FOOTBALL PATHS
# =========================================================

FOOTBALL_MASTER_DIR = FOOTBALL_DATA_DIR / "master"
FOOTBALL_RAW_DIR = FOOTBALL_DATA_DIR / "raw"
FOOTBALL_EXPORTS_DIR = FOOTBALL_DATA_DIR / "exports"

FOOTBALL_HISTORY_FILE = (
    FOOTBALL_MASTER_DIR / "football_master_all_leagues.xlsx"
)

FOOTBALL_FIXTURES_FILE = (
    FOOTBALL_MASTER_DIR / "football_fixtures.xlsx"
)

FOOTBALL_FIXTURES_CSV_FILE = (
    FOOTBALL_MASTER_DIR / "football_fixtures.csv"
)

FOOTBALL_RAW_FIXTURES_DIR = (
    FOOTBALL_RAW_DIR / "fixtures"
)

FOOTBALL_MANUAL_FIXTURES_CSV_FILE = (
    FOOTBALL_RAW_FIXTURES_DIR / "new_league_fixtures.csv"
)

FOOTBALL_MANUAL_FIXTURES_XLSX_FILE = (
    FOOTBALL_RAW_FIXTURES_DIR / "new_league_fixtures.xlsx"
)

FOOTBALL_FIXTURE_PREDICTIONS_FILE = (
    FOOTBALL_EXPORTS_DIR / "predictions" / "football_fixture_predictions.xlsx"
)

FOOTBALL_ENSEMBLE_PREDICTIONS_FILE = (
    FOOTBALL_EXPORTS_DIR / "predictions" / "football_ensemble_predictions.xlsx"
)

FOOTBALL_BACKTEST_HISTORY_FILE = (
    FOOTBALL_EXPORTS_DIR / "backtesting" / "football_fixture_backtest_history.xlsx"
)


# =========================================================
# APP PATHS
# =========================================================

APP_DIR = SRC_DIR / "app"
APP_PAGES_DIR = APP_DIR / "pages"
APP_COMPONENTS_DIR = APP_DIR / "components"
APP_STYLES_DIR = APP_DIR / "styles"
APP_ASSETS_DIR = APP_DIR / "assets"


# =========================================================
# HELPERS
# =========================================================

def ensure_directory(path: Path) -> Path:
    path.mkdir(
        parents=True,
        exist_ok=True
    )

    return path


def ensure_parent_directory(path: Path) -> Path:
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    return path


def path_exists(path: Path) -> bool:
    return path.exists()


def get_project_root() -> Path:
    return PROJECT_ROOT


def get_database_file() -> Path:
    return DATABASE_FILE


def get_path_summary() -> dict:
    return {
        "PROJECT_ROOT": PROJECT_ROOT,
        "SRC_DIR": SRC_DIR,
        "DATA_DIR": DATA_DIR,
        "DATABASE_FILE": DATABASE_FILE,
        "LOTTERY_MASTER_FILE": LOTTERY_MASTER_FILE,
        "FOOTBALL_HISTORY_FILE": FOOTBALL_HISTORY_FILE,
        "FOOTBALL_FIXTURES_FILE": FOOTBALL_FIXTURES_FILE,
        "FOOTBALL_ENSEMBLE_PREDICTIONS_FILE": FOOTBALL_ENSEMBLE_PREDICTIONS_FILE,
    }


def print_path_summary():
    print("======================================")
    print("HEXAGRANDHOUSE PATH SUMMARY")
    print("======================================")

    for name, value in get_path_summary().items():
        print(f"{name}: {value}")

    print("======================================")