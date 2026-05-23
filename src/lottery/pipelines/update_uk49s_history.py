from src.lottery.scrapers.uk49s_scraper import scrape_uk49s_history
from src.lottery.outputs.lottery_master_writer import append_history_rows


# =========================================================
# UK49S HISTORY UPDATE PIPELINE
# =========================================================

def update_uk49s_history():
    print("\n======================================")
    print("UPDATE UK49S HISTORY")
    print("======================================")
    print("Source: ZA National Lottery recent UK49s pages")
    print("Draws : Lunchtime + Teatime")
    print("======================================\n")

    rows = scrape_uk49s_history()

    result = append_history_rows(
        new_rows=rows,
        update_type="UK49s Web Scrape",
        game_family="UK49s",
        game_name="UK49s Lunchtime / UK49s Teatime",
        draw_type="Lunchtime + Teatime",
        notes="Updated recent UK49s Lunchtime and Teatime historical results from ZA National Lottery."
    )

    print("\n======================================")
    print("UK49S UPDATE COMPLETE")
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
    update_uk49s_history()


if __name__ == "__main__":
    main()