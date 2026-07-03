from __future__ import annotations

import platform
import sqlite3
from pathlib import Path

from src.core.constants import APP_NAME, APP_VERSION
from src.core.paths import (
    PROJECT_ROOT,
    SRC_DIR,
    DATA_DIR,
    DATABASE_FILE,
)
from src.data.database import (
    database_exists,
    get_database_summary,
)
from src.services.home_service import get_home_dashboard_data
from src.services.football_service import get_football_dashboard_data
from src.services.lottery_service import get_lottery_dashboard_data
from src.services.results_service import get_results_dashboard_data
from src.services.accuracy_service import get_accuracy_dashboard_data


REFRESH_MARKER_FILE = DATA_DIR / "last_cloud_refresh.txt"


def get_file_size_mb(path: Path) -> float:
    if not path.exists():
        return 0.0

    return round(path.stat().st_size / (1024 * 1024), 2)


def read_refresh_marker() -> str:
    if not REFRESH_MARKER_FILE.exists():
        return "Not available"

    try:
        return REFRESH_MARKER_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return "Unreadable"


def service_status(name: str, passed: bool, detail: str = "") -> dict:
    return {
        "Service": name,
        "Status": "Healthy" if passed else "Warning",
        "Detail": detail,
    }


def get_platform_health() -> dict:
    db_summary = get_database_summary()

    return {
        "database_exists": database_exists(),
        "database_file": str(DATABASE_FILE),
        "database_size_mb": get_file_size_mb(DATABASE_FILE),
        "database_summary": db_summary,
        "total_rows": int(db_summary["RowCount"].sum()) if not db_summary.empty else 0,
        "table_count": len(db_summary),
        "last_refresh": read_refresh_marker(),
    }


def get_service_health() -> list[dict]:
    statuses = []

    try:
        home = get_home_dashboard_data()
        statuses.append(
            service_status(
                "Home Service",
                bool(home),
                f"{home.get('total_rows', 0):,} platform rows",
            )
        )
    except Exception as exc:
        statuses.append(service_status("Home Service", False, str(exc)))

    try:
        football = get_football_dashboard_data(limit=100)
        statuses.append(
            service_status(
                "Football Service",
                True,
                f"{football['kpis'].get('fixtures', 0)} fixtures | {football['kpis'].get('predictions', 0)} predictions",
            )
        )
    except Exception as exc:
        statuses.append(service_status("Football Service", False, str(exc)))

    try:
        lottery = get_lottery_dashboard_data(limit=100)
        statuses.append(
            service_status(
                "Lottery Service",
                True,
                f"{lottery['kpis'].get('result_count', 0)} results | {lottery['kpis'].get('prediction_count', 0)} predictions",
            )
        )
    except Exception as exc:
        statuses.append(service_status("Lottery Service", False, str(exc)))

    try:
        results = get_results_dashboard_data(days=7)
        statuses.append(
            service_status(
                "Results Service",
                True,
                f"{results['kpis'].get('lottery_results', 0)} lottery | {results['kpis'].get('football_results', 0)} football",
            )
        )
    except Exception as exc:
        statuses.append(service_status("Results Service", False, str(exc)))

    try:
        accuracy = get_accuracy_dashboard_data()
        statuses.append(
            service_status(
                "Accuracy Service",
                True,
                f"{accuracy['kpis'].get('fixtures_scored', 0)} scored fixtures",
            )
        )
    except Exception as exc:
        statuses.append(service_status("Accuracy Service", False, str(exc)))

    return statuses


def get_environment_info() -> dict:
    return {
        "App Name": APP_NAME,
        "App Version": APP_VERSION,
        "Python": platform.python_version(),
        "Platform": platform.platform(),
        "SQLite": sqlite3.sqlite_version,
        "Project Root": str(PROJECT_ROOT),
        "Source Directory": str(SRC_DIR),
        "Data Directory": str(DATA_DIR),
    }


def get_admin_dashboard_data() -> dict:
    platform_health = get_platform_health()
    service_health = get_service_health()
    environment_info = get_environment_info()

    healthy_services = sum(
        1 for service in service_health
        if service["Status"] == "Healthy"
    )

    return {
        "platform": platform_health,
        "services": service_health,
        "environment": environment_info,
        "kpis": {
            "database": "Online" if platform_health["database_exists"] else "Missing",
            "services": f"{healthy_services}/{len(service_health)}",
            "total_rows": platform_health["total_rows"],
            "last_refresh": platform_health["last_refresh"],
        },
    }