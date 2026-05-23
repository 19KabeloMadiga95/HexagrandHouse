import argparse
from datetime import datetime

from src.lottery.pipelines.update_powerball_history import update_powerball_history
from src.lottery.pipelines.update_lotto_history import update_lotto_history
from src.lottery.pipelines.update_daily_lotto_history import update_daily_lotto_history
from src.lottery.pipelines.update_uk49s_history import update_uk49s_history


# =========================================================
# UPDATE ALL LOTTERY HISTORY PIPELINE
# =========================================================

def update_all_lottery_history(start_year=None, end_year=None):
    print("\n======================================")
    print("HEXAGRANDHOUSE LOTTERY HISTORY UPDATE")
    print("======================================")
    print(f"Run time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Start year: {start_year}")
    print(f"End year  : {end_year}")
    print("======================================\n")

    results = []

    steps = [
        {
            "name": "PowerBall",
            "runner": lambda: update_powerball_history(
                start_year=start_year,
                end_year=end_year
            ),
        },
        {
            "name": "Lotto",
            "runner": lambda: update_lotto_history(
                start_year=start_year,
                end_year=end_year
            ),
        },
        {
            "name": "Daily Lotto",
            "runner": lambda: update_daily_lotto_history(
                start_year=start_year,
                end_year=end_year
            ),
        },
        {
            "name": "UK49s",
            "runner": update_uk49s_history,
        },
    ]

    for step in steps:
        name = step["name"]

        print("\n--------------------------------------")
        print(f"STARTING: {name}")
        print("--------------------------------------")

        try:
            result = step["runner"]()

            result["engine"] = name
            result["error"] = ""

            results.append(result)

        except Exception as e:
            print(f"\n❌ {name} update failed: {e}")

            results.append({
                "engine": name,
                "rows_fetched": 0,
                "rows_added": 0,
                "rows_skipped": 0,
                "status": "Failed",
                "error": str(e),
            })

    print("\n======================================")
    print("ALL LOTTERY HISTORY UPDATE COMPLETE")
    print("======================================")

    total_fetched = 0
    total_added = 0
    total_skipped = 0

    for result in results:
        engine = result.get("engine", "")
        fetched = result.get("rows_fetched", 0)
        added = result.get("rows_added", 0)
        skipped = result.get("rows_skipped", 0)
        status = result.get("status", "")
        error = result.get("error", "")

        total_fetched += fetched
        total_added += added
        total_skipped += skipped

        print(
            f"{engine:<15} | "
            f"Fetched: {fetched:<6} | "
            f"Added: {added:<6} | "
            f"Skipped: {skipped:<6} | "
            f"Status: {status}"
        )

        if error:
            print(f"  Error: {error}")

    print("--------------------------------------")
    print(f"{'TOTAL':<15} | Fetched: {total_fetched:<6} | Added: {total_added:<6} | Skipped: {total_skipped:<6}")
    print("======================================\n")

    return results


# =========================================================
# CLI
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description="Update all lottery historical data engines."
    )

    parser.add_argument(
        "--start-year",
        type=int,
        default=None,
        help="Optional start year for games with yearly archives, e.g. 2015"
    )

    parser.add_argument(
        "--end-year",
        type=int,
        default=None,
        help="Optional end year for games with yearly archives, e.g. 2026"
    )

    args = parser.parse_args()

    update_all_lottery_history(
        start_year=args.start_year,
        end_year=args.end_year
    )


if __name__ == "__main__":
    main()