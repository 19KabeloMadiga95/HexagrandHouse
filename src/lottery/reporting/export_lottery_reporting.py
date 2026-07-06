from __future__ import annotations

from datetime import datetime
from typing import Any

from src.lottery.reporting.daily_lottery_summary_generator import export_daily_summary
from src.lottery.reporting.executive_lottery_report import export_executive_report
from src.lottery.scoring.model_performance_dashboard import export_model_performance_dashboard
from src.lottery.scoring.unified_model_performance_dashboard import export_unified_model_performance_dashboard


# =========================================================
# SQLITE-FIRST LOTTERY REPORTING RUNNER
# =========================================================


def _sum_rows(result: Any) -> int:
    if isinstance(result, dict):
        total = 0
        for value in result.values():
            try:
                total += int(value)
            except Exception:
                pass
        return total
    return 0


def export_lottery_reporting() -> dict[str, Any]:
    started_at = datetime.now()

    print("\n======================================")
    print("HEXAGRANDHOUSE LOTTERY REPORTING")
    print("SQLite-first runtime mode")
    print("======================================")
    print(f"Started: {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print("======================================\n")

    unified = export_unified_model_performance_dashboard()
    powerball = export_model_performance_dashboard()
    daily = export_daily_summary()
    executive = export_executive_report()

    finished_at = datetime.now()
    duration = round((finished_at - started_at).total_seconds(), 2)
    total_rows = _sum_rows(unified) + _sum_rows(powerball) + _sum_rows(daily) + _sum_rows(executive)

    print("\n======================================")
    print("LOTTERY REPORTING COMPLETE")
    print("======================================")
    print(f"Finished: {finished_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration} sec")
    print(f"Rows    : {total_rows}")
    print("======================================\n")

    return {
        "Status": "Success",
        "DurationSeconds": duration,
        "Rows": total_rows,
        "Unified": unified,
        "PowerBall": powerball,
        "Daily": daily,
        "Executive": executive,
    }


def main() -> dict[str, Any]:
    return export_lottery_reporting()


if __name__ == "__main__":
    main()
