# =========================================================
# HEXAGRANDHOUSE CORE CONSTANTS
# =========================================================

APP_NAME = "HexagrandHouse"
APP_VERSION = "2.0-local-foundation"


# =========================================================
# GENERAL SETTINGS
# =========================================================

RNG_SEED = 42
CACHE_TTL_SECONDS = 300

DEFAULT_TOP_PREDICTIONS = 10
DEFAULT_SIMULATION_COUNT = 100

DEFAULT_LOOKBACK_DAYS = 365
DEFAULT_RECENT_DAYS = 7


# =========================================================
# LOTTERY SETTINGS
# =========================================================

LOTTERY_DEFAULT_TOP_PREDICTIONS = 10
LOTTERY_DEFAULT_CONFIDENCE_DECIMALS = 2

LOTTERY_LOW_CONFIDENCE_THRESHOLD = 60
LOTTERY_MEDIUM_CONFIDENCE_THRESHOLD = 75
LOTTERY_HIGH_CONFIDENCE_THRESHOLD = 85


# =========================================================
# FOOTBALL SETTINGS
# =========================================================

FOOTBALL_DEFAULT_TOP_PICKS = 25
FOOTBALL_DEFAULT_FIXTURE_LIMIT = 200

FOOTBALL_LOW_CONFIDENCE_THRESHOLD = 60
FOOTBALL_MEDIUM_CONFIDENCE_THRESHOLD = 75
FOOTBALL_HIGH_CONFIDENCE_THRESHOLD = 85

FOOTBALL_RECENT_RESULTS_DAYS = 14


# =========================================================
# DATABASE SETTINGS
# =========================================================

SQLITE_TIMEOUT_SECONDS = 30

DATABASE_TABLES = {
    "lottery_history": "lottery_history",
    "lottery_predictions": "lottery_predictions",
    "football_history": "football_history",
    "football_fixtures": "football_fixtures",
    "football_predictions": "football_predictions",
    "football_ensemble_predictions": "football_ensemble_predictions",
    "football_backtest_history": "football_backtest_history",
}


# =========================================================
# OUTPUT SETTINGS
# =========================================================

EXPORT_EXCEL = True
EXPORT_CSV = True

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# =========================================================
# STATUS VALUES
# =========================================================

STATUS_SUCCESS = "Success"
STATUS_WARNING = "Warning"
STATUS_FAILED = "Failed"
STATUS_SKIPPED = "Skipped"


def get_confidence_label(
    score,
    low_threshold=LOTTERY_LOW_CONFIDENCE_THRESHOLD,
    medium_threshold=LOTTERY_MEDIUM_CONFIDENCE_THRESHOLD,
    high_threshold=LOTTERY_HIGH_CONFIDENCE_THRESHOLD,
):
    try:
        score = float(score)
    except Exception:
        return "Unrated"

    if score >= high_threshold:
        return "Elite"

    if score >= medium_threshold:
        return "High"

    if score >= low_threshold:
        return "Medium"

    if score > 0:
        return "Low"

    return "Unrated"


def print_constants_summary():
    print("======================================")
    print("HEXAGRANDHOUSE CONSTANTS")
    print("======================================")
    print(f"APP_NAME: {APP_NAME}")
    print(f"APP_VERSION: {APP_VERSION}")
    print(f"RNG_SEED: {RNG_SEED}")
    print(f"CACHE_TTL_SECONDS: {CACHE_TTL_SECONDS}")
    print(f"DEFAULT_TOP_PREDICTIONS: {DEFAULT_TOP_PREDICTIONS}")
    print("======================================")