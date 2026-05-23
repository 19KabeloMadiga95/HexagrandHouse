import argparse

from src.lottery.scrapers.lotto_scraper import scrape_lotto_history
from src.lottery.outputs.lottery_master_writer import append_history_rows


# =========================================================
# LOTTO HISTORY UPDATE PIPELINE
# =========================================================

def update_lotto_history(start_year=None, end_year=None):
    print("\n======================================")
    print("UPDATE LOTTO HISTORY")
    print("======================================")
    print(f"Start year: {start_year}")
    print(f"End year  : {end_year}")
    print("======================================\n")

    rows = scrape_lotto_history(
        start_year=start_year,
        end_year=end_year
    )

    result = append_history_rows(
        new_rows=rows,
        update_type="Lotto Web Scrape",
        game_family="Lotto",
        game_name="Lotto / Lotto Plus 1 / Lotto Plus 2",
        draw_type="Main + Plus 1 + Plus 2",
        notes="Updated Lotto, Lotto Plus 1, and Lotto Plus 2 historical results."
    )

    print("\n======================================")
    print("LOTTO UPDATE COMPLETE")
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
        description="Update Lotto, Lotto Plus 1, and Lotto Plus 2 history."
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

    update_lotto_history(
        start_year=args.start_year,
        end_year=args.end_year
    )


if __name__ == "__main__":
    main()