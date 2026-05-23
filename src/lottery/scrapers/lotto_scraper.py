import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from src.lottery.analytics.historical_schema import build_history_row


# =========================================================
# LOTTO SOURCE CONFIG
# =========================================================

SOURCE_NAME = "za.national-lottery.com"

LOTTO_HISTORY_URL = "https://za.national-lottery.com/lotto/results/history"
LOTTO_PLUS_1_HISTORY_URL = "https://za.national-lottery.com/lotto-plus-1/results/history"
LOTTO_PLUS_2_HISTORY_URL = "https://za.national-lottery.com/lotto-plus-2/results/history"

GAME_CONFIGS = [
    {
        "game_family": "Lotto",
        "game_name": "Lotto",
        "draw_type": "Main",
        "history_url": LOTTO_HISTORY_URL,
        "archive_pattern": "https://za.national-lottery.com/lotto/results/{year}-archive",
    },
    {
        "game_family": "Lotto",
        "game_name": "Lotto Plus 1",
        "draw_type": "Plus 1",
        "history_url": LOTTO_PLUS_1_HISTORY_URL,
        "archive_pattern": "https://za.national-lottery.com/lotto-plus-1/results/{year}-archive",
    },
    {
        "game_family": "Lotto",
        "game_name": "Lotto Plus 2",
        "draw_type": "Plus 2",
        "history_url": LOTTO_PLUS_2_HISTORY_URL,
        "archive_pattern": "https://za.national-lottery.com/lotto-plus-2/results/{year}-archive",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_text(value):
    if value is None:
        return ""

    value = str(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def fetch_html(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def parse_jackpot(value):
    value = clean_text(value)

    if not value:
        return None

    value = value.replace("R", "")
    value = value.replace(",", "")
    value = value.strip()

    try:
        return float(value)
    except ValueError:
        return None


def extract_years_from_history_page(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    years = set()

    for link in soup.find_all("a"):
        text = clean_text(link.get_text())

        if re.fullmatch(r"\d{4}", text):
            years.add(int(text))

    return sorted(years, reverse=True)


# =========================================================
# ARCHIVE PARSER
# =========================================================

def parse_archive_page(
    game_family,
    game_name,
    draw_type,
    year,
    url
):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(" ")
    text = clean_text(text)

    date_pattern = re.compile(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+"
        r"(\d{1,2})\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
        r"(\d{4})"
    )

    matches = list(date_pattern.finditer(text))

    rows = []

    for idx, match in enumerate(matches):
        day = int(match.group(2))
        month_name = match.group(3)
        draw_year = int(match.group(4))

        month = MONTHS.get(month_name)

        if month is None:
            continue

        draw_date = datetime(draw_year, month, day).date()

        block_start = match.end()
        block_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[block_start:block_end]

        numbers = re.findall(r"(?<![\d.])\d{1,2}(?![\d.])", block)

        # Lotto normally has 6 regular numbers + bonus = 7 numbers
        if len(numbers) < 6:
            continue

        numbers = [int(n) for n in numbers]

        regular_numbers = numbers[:6]

        bonus = None
        if len(numbers) >= 7:
            bonus = numbers[6]

        jackpot_match = re.search(r"R[\d,]+(?:\.\d{1,2})?", block)
        jackpot = parse_jackpot(jackpot_match.group(0)) if jackpot_match else None

        outcome_match = re.search(r"\b(Roll|Won|Rolled Over)\b", block)
        outcome = outcome_match.group(1) if outcome_match else ""

        row = build_history_row(
            game_family=game_family,
            game_name=game_name,
            draw_type=draw_type,
            draw_date=draw_date,
            n1=regular_numbers[0],
            n2=regular_numbers[1],
            n3=regular_numbers[2],
            n4=regular_numbers[3],
            n5=regular_numbers[4],
            n6=regular_numbers[5],
            bonus=bonus,
            draw_number=None,
            jackpot=jackpot,
            outcome=outcome,
            source_name=SOURCE_NAME,
            source_url=url,
        )

        rows.append(row)

    return rows


# =========================================================
# MAIN SCRAPER
# =========================================================

def scrape_lotto_history(
    start_year=None,
    end_year=None,
    sleep_seconds=0.3
):
    all_rows = []

    for config in GAME_CONFIGS:
        game_name = config["game_name"]
        history_url = config["history_url"]
        archive_pattern = config["archive_pattern"]

        print(f"\nFetching available years for {game_name}...")

        years = extract_years_from_history_page(history_url)

        if start_year is not None:
            years = [year for year in years if year >= start_year]

        if end_year is not None:
            years = [year for year in years if year <= end_year]

        print(f"{game_name}: years found = {years}")

        for year in years:
            url = archive_pattern.format(year=year)

            try:
                print(f"Scraping {game_name} {year}: {url}")

                rows = parse_archive_page(
                    game_family=config["game_family"],
                    game_name=config["game_name"],
                    draw_type=config["draw_type"],
                    year=year,
                    url=url,
                )

                all_rows.extend(rows)

                print(f"Rows fetched: {len(rows)}")

                time.sleep(sleep_seconds)

            except Exception as e:
                print(f"Failed {game_name} {year}: {e}")

    return all_rows


# =========================================================
# QUICK TEST
# =========================================================

if __name__ == "__main__":
    rows = scrape_lotto_history(
        start_year=2026,
        end_year=2026
    )

    print("\n======================================")
    print("LOTTO SCRAPER TEST COMPLETE")
    print("======================================")
    print(f"Rows scraped: {len(rows)}")

    if rows:
        print("\nSample row:")
        print(rows[0])