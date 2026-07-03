from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import logging
import sys
import time


from src.core.paths import LOGS_DIR, ensure_directory


# ==========================================================
# INITIALISE LOG DIRECTORY
# ==========================================================

ensure_directory(LOGS_DIR)


LOG_FILE = LOGS_DIR / (
    f"hexagrandhouse_{datetime.now():%Y%m%d}.log"
)


# ==========================================================
# LOGGER
# ==========================================================

LOGGER = logging.getLogger("HexagrandHouse")

if not LOGGER.handlers:

    LOGGER.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    LOGGER.addHandler(console)
    LOGGER.addHandler(file_handler)


# ==========================================================
# SIMPLE LOG FUNCTIONS
# ==========================================================

def info(message: str):
    LOGGER.info(message)


def warning(message: str):
    LOGGER.warning(message)


def error(message: str):
    LOGGER.error(message)


def success(message: str):
    LOGGER.info(f"SUCCESS | {message}")


def divider(char: str = "="):
    LOGGER.info(char * 70)


def section(title: str):
    divider("=")
    LOGGER.info(title.upper())
    divider("=")


# ==========================================================
# TIMERS
# ==========================================================

@contextmanager
def timer(name: str):
    start = time.perf_counter()

    LOGGER.info(f"START : {name}")

    try:
        yield

        elapsed = time.perf_counter() - start

        LOGGER.info(
            f"END   : {name} "
            f"({elapsed:.2f} sec)"
        )

    except Exception:

        elapsed = time.perf_counter() - start

        LOGGER.exception(
            f"FAILED: {name} "
            f"({elapsed:.2f} sec)"
        )

        raise


# ==========================================================
# PIPELINE BANNER
# ==========================================================

def pipeline_banner(name: str):

    divider("=")

    LOGGER.info(f"HEXAGRANDHOUSE : {name}")

    LOGGER.info(
        f"Started : "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    )

    divider("=")


def pipeline_complete(name: str):

    divider("=")

    LOGGER.info(f"{name} COMPLETE")

    LOGGER.info(
        f"Finished : "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    )

    divider("=")


# ==========================================================
# FILE HELPERS
# ==========================================================

def log_file(path: Path):

    if path.exists():

        LOGGER.info(
            f"FOUND : {path.name}"
        )

    else:

        LOGGER.warning(
            f"MISSING : {path}"
        )


def log_dataframe(name: str, df):

    try:

        rows = len(df)

    except Exception:

        rows = "Unknown"

    LOGGER.info(
        f"{name} | Rows = {rows}"
    )


# ==========================================================
# SUMMARY
# ==========================================================

def print_environment():

    section("Environment")

    LOGGER.info(
        f"Python : {sys.version.split()[0]}"
    )

    LOGGER.info(
        f"Working Directory : {Path.cwd()}"
    )

    LOGGER.info(
        f"Log File : {LOG_FILE}"
    )