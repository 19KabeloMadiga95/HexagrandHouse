from __future__ import annotations

from datetime import datetime
from time import perf_counter

from src.football.models.corners_model import export_corners_predictions
from src.football.models.ensemble_engine import export_football_ensemble_predictions
from src.football.models.goals_model import export_goals_predictions
from src.football.models.result_model import export_result_predictions


# =========================================================
# FOOTBALL MODEL EXPORT ORCHESTRATOR
# =========================================================

def _run_step(label: str, func):
    print("\n" + "-" * 38)
    print(f"RUNNING: {label}")
    print("-" * 38)

    start = perf_counter()
    df = func()
    duration = perf_counter() - start
    rows = len(df) if df is not None else 0

    print(f"SUCCESS: {label}")
    print(f"Rows    : {rows}")
    print(f"Duration: {duration:.2f} sec")

    return {
        "Step": label,
        "Rows": rows,
        "Status": "Success",
        "DurationSec": round(duration, 2),
    }


def export_all_football_models() -> list[dict]:
    print("=" * 38)
    print("HEXAGRANDHOUSE FOOTBALL MODELS")
    print("SQLite-first runtime mode")
    print("=" * 38)
    print(f"Run time: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 38)

    results = []

    results.append(_run_step("Result Model", export_result_predictions))
    results.append(_run_step("Goals Model", export_goals_predictions))
    results.append(_run_step("Corners Model", export_corners_predictions))
    results.append(_run_step("Football Ensemble", export_football_ensemble_predictions))

    print("\n" + "=" * 38)
    print("FOOTBALL MODEL EXPORT COMPLETE")
    print("=" * 38)

    for row in results:
        print(
            f"{row['Step']:<24} | Rows: {row['Rows']:<8} | "
            f"Status: {row['Status']}"
        )

    print("=" * 38)

    return results


def export_football_models() -> list[dict]:
    """Backward-compatible callable used by the heavy football model rebuild cycle."""
    return export_all_football_models()


def main() -> None:
    export_all_football_models()


if __name__ == "__main__":
    main()
