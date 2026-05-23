import argparse

from src.lottery.scrapers.daily_lotto_scraper import scrape_daily_lotto_history
from src.lottery.outputs.lottery_master_writer import append_history_rows


# =========================================================
# DAILY LOTTO HISTORY UPDATE PIPELINE
# =========================================================

def update_daily_lotto_history(start_year=None, end_year=None):
    print("\n======================================")
    print("UPDATE DAILY LOTTO HISTORY")
    print("======================================")
    print(f"Start year: {start_year}")
    print(f"End year  : {end_year}")
    print("======================================\n")

    rows = scrape_daily_lotto_history(
        start_year=start_year,
        end_year=end_year
    )

    result = append_history_rows(
        new_rows=rows,
        update_type="Daily Lotto Web Scrape",
        game_family="Daily Lotto",
        game_name="Daily Lotto",
        draw_type="Main",
        notes="Updated Daily Lotto historical results."
    )

    print("\n======================================")
    print("DAILY LOTTO UPDATE COMPLETE")
    print("======================================")
    print(f"Rows fetched : {result['rows_fetched']}")
    print(f"Rows added   : {result['rows_added']}")
    print(f"Rows skipped : {result['rows_skipped']}")
    print(f"Status       : {result['status']}")
    print("======================================\n")

    return result


# =========================================================
# CLI
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description="Update Daily Lotto history."
    )

    parser.add_argument(
        "--start-year",
        type=int,
        default=None,
        help="Optional start year, e.g. 2015"
    )

    parser.add_argument(
        "--end-year",
        type=int,
        default=None,
        help="Optional end year, e.g. 2026"
    )

    args = parser.parse_args()

    update_daily_lotto_history(
        start_year=args.start_year,
        end_year=args.end_year
    )


if __name__ == "__main__":
    main()
    