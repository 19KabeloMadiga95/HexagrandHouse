import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from src.lottery.analytics.historical_schema import build_history_row


# =========================================================
# UK49S ZA SOURCE CONFIG
# =========================================================

SOURCE_NAME = "za.national-lottery.com"

UK49S_LUNCHTIME_URL = "https://za.national-lottery.com/uk-49s/results/lunchtime"
UK49S_TEATIME_URL = "https://za.national-lottery.com/uk-49s/results/teatime"

GAME_CONFIGS = [
    {
        "game_family": "UK49s",
        "game_name": "UK49s Lunchtime",
        "draw_type": "Lunchtime",
        "url": UK49S_LUNCHTIME_URL,
    },
    {
        "game_family": "UK49s",
        "game_name": "UK49s Teatime",
        "draw_type": "Teatime",
        "url": UK49S_TEATIME_URL,
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
# HELPERS
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


def get_page_lines(html):
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    lines = []

    for line in soup.get_text("\n").splitlines():
        line = clean_text(line)

        if line:
            lines.append(line)

    return lines


def is_weekday(value):
    return value in {
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    }


def parse_date_from_parts(day_name, date_text):
    """
    Example:
    day_name = Friday
    date_text = 8 May 2026
    """
    parts = clean_text(date_text).split()

    if len(parts) != 3:
        return None

    day = int(parts[0])
    month = MONTHS.get(parts[1])
    year = int(parts[2])

    if month is None:
        return None

    return datetime(year, month, day).date()


def is_number(value):
    return re.fullmatch(r"\d{1,2}", clean_text(value)) is not None


# =========================================================
# PARSER
# =========================================================

def parse_uk49s_page(config):
    url = config["url"]

    html = fetch_html(url)
    lines = get_page_lines(html)

    rows = []

    i = 0

    while i < len(lines):
        current = lines[i]

        if not is_weekday(current):
            i += 1
            continue

        if i + 1 >= len(lines):
            i += 1
            continue

        date_text = lines[i + 1]

        if not re.fullmatch(
            r"\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December) \d{4}",
            date_text
        ):
            i += 1
            continue

        draw_date = parse_date_from_parts(current, date_text)

        numbers = []
        j = i + 2

        while j < len(lines) and len(numbers) < 7:
            if is_number(lines[j]):
                numbers.append(int(lines[j]))
            j += 1

        if draw_date is not None and len(numbers) == 7:
            regular_numbers = numbers[:6]
            bonus = numbers[6]

            row = build_history_row(
                game_family=config["game_family"],
                game_name=config["game_name"],
                draw_type=config["draw_type"],
                draw_date=draw_date,
                n1=regular_numbers[0],
                n2=regular_numbers[1],
                n3=regular_numbers[2],
                n4=regular_numbers[3],
                n5=regular_numbers[4],
                n6=regular_numbers[5],
                bonus=bonus,
                draw_number=None,
                jackpot=None,
                outcome="",
                source_name=SOURCE_NAME,
                source_url=url,
            )

            rows.append(row)

        i = j

    return rows


# =========================================================
# MAIN SCRAPER
# =========================================================

def scrape_uk49s_history(sleep_seconds=0.3):
    all_rows = []

    print("\nFetching UK49s recent history from ZA National Lottery pages...")

    for config in GAME_CONFIGS:
        print(f"Scraping {config['game_name']}: {config['url']}")

        try:
            rows = parse_uk49s_page(config)

            all_rows.extend(rows)

            print(f"Rows fetched: {len(rows)}")

            time.sleep(sleep_seconds)

        except Exception as e:
            print(f"Failed {config['game_name']}: {e}")

    return all_rows


# =========================================================
# QUICK TEST
# =========================================================

if __name__ == "__main__":
    rows = scrape_uk49s_history()

    print("\n======================================")
    print("UK49S ZA SCRAPER TEST COMPLETE")
    print("======================================")
    print(f"Rows scraped: {len(rows)}")

    if rows:
        print("\nSample row:")
        print(rows[0])