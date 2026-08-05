"""Generate copy-ready WhatsApp Channel posts for HexaGrandBet.

This script does NOT post to WhatsApp automatically.
It reads the refreshed SQLite runtime database and writes text files that can
be copied into the WhatsApp Channel after the daily GitHub Actions cycle.

Outputs:
    social_posts/whatsapp_channel_today.txt
    social_posts/whatsapp_channel_weekly_plan.txt

Usage:
    python tools/generate_whatsapp_channel_post.py
    python tools/generate_whatsapp_channel_post.py --db data/hexagrandhouse.db --site-url https://hexagrandbet.com
"""

from __future__ import annotations

import argparse
import datetime as dt
import random
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


DEFAULT_DB_PATH = Path("data/hexagrandhouse.db")
DEFAULT_OUT_DIR = Path("social_posts")
DEFAULT_SITE_URL = "https://hexagrandbet.com"
TEXT_ENCODING = "utf-8-sig"

GAME_PRIORITY = [
    "Daily Lotto",
    "Lotto",
    "PowerBall",
    "UK49s Lunchtime",
    "UK49s Teatime",
]

DISCLAIMER = "18+ | Analytics only | No guarantees"


# -----------------------------------------------------------------------------
# Generic SQLite helpers
# -----------------------------------------------------------------------------

def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def table_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    if not table_exists(conn, table_name):
        return []
    return [row[1] for row in conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()]


def fetch_rows(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def safe_str(value: Any, fallback: str = "-") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "nat"}:
        return fallback
    return text


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def pct(value: Any) -> str:
    num = safe_float(value)
    if num is None:
        return "-"
    # Model probabilities are usually 0-1; some scores are already 0-100.
    if 0 <= num <= 1:
        num *= 100
    return f"{num:.1f}%"


def today_local() -> dt.date:
    # GitHub Actions runs in UTC. South Africa is UTC+2 and has no DST.
    return (dt.datetime.now(dt.UTC) + dt.timedelta(hours=2)).date()


def week_start_monday(day: dt.date) -> dt.date:
    return day - dt.timedelta(days=day.weekday())


def first_existing(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    lookup = {col.lower(): col for col in columns}
    for candidate in candidates:
        found = lookup.get(candidate.lower())
        if found:
            return found
    return None


# -----------------------------------------------------------------------------
# Football section
# -----------------------------------------------------------------------------

def best_football_pick(conn: sqlite3.Connection, day: dt.date) -> dict[str, Any] | None:
    """Return best current football pick from the most public/current tables."""
    table_preferences = [
        (
            "football_value_bets",
            [
                "ValueRank ASC",
                "ValueBetScore DESC",
                "ModelProbability DESC",
                "ConfidenceScore DESC",
            ],
        ),
        (
            "football_top_plays",
            [
                "TopPlayRank ASC",
                "TopPlayScore DESC",
                "ModelProbability DESC",
                "ConfidenceScore DESC",
            ],
        ),
        (
            "football_fixture_predictions",
            [
                "ModelProbability DESC",
                "ConfidenceScore DESC",
                "EnsembleConfidenceScore DESC",
            ],
        ),
    ]

    for table, order_candidates in table_preferences:
        columns = table_columns(conn, table)
        if not columns:
            continue

        date_col = first_existing(columns, ["FixtureDate", "MatchDate", "Date"])
        order_terms = []
        for term in order_candidates:
            col = term.split()[0]
            if col in columns:
                order_terms.append(term)
        order_sql = ", ".join(order_terms) if order_terms else "rowid ASC"

        where_sql = ""
        params: tuple[Any, ...] = ()
        if date_col:
            where_sql = f"WHERE date({date_col}) >= date(?)"
            params = (day.isoformat(),)

        query = f"""
            SELECT *
            FROM {table}
            {where_sql}
            ORDER BY {order_sql}
            LIMIT 1
        """
        rows = fetch_rows(conn, query, params)
        if rows:
            row = rows[0]
            row["_source_table"] = table
            return row

    return None


def format_football_block(pick: dict[str, Any] | None) -> str:
    if not pick:
        return "⚽ Football: No strong pick today"

    home = safe_str(pick.get("HomeTeam"), "Home")
    away = safe_str(pick.get("AwayTeam"), "Away")
    league = safe_str(pick.get("League"), "Football")
    kickoff = safe_str(pick.get("KickoffTime"), "")
    signal = safe_str(
        pick.get("PrimaryMarketSignal")
        or pick.get("PredictedResult")
        or pick.get("Market"),
        "Review pick",
    )
    confidence = safe_str(pick.get("ConfidenceLabel") or pick.get("ValueRating"), "Review")
    probability = pct(
        pick.get("ModelProbability")
        or pick.get("ConfidenceScore")
        or pick.get("EnsembleConfidenceScore")
    )

    fixture_line = f"⚽ {home} vs {away}"
    context_parts = [part for part in [league, kickoff] if part]
    context_line = " • ".join(context_parts)

    lines = [
        fixture_line,
        f"Pick: {signal}",
        f"Strength: {confidence} ({probability})",
    ]
    if context_line:
        lines.insert(1, context_line)

    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Lottery section
# -----------------------------------------------------------------------------

def normalize_game_name(raw: Any) -> str:
    text = safe_str(raw, "").strip()
    if not text:
        return ""
    compact = re.sub(r"\s+", " ", text).strip().lower()

    if "daily" in compact and "lotto" in compact:
        return "Daily Lotto"
    if "power" in compact:
        return "PowerBall"
    if "uk49" in compact and "lunch" in compact:
        return "UK49s Lunchtime"
    if "uk49" in compact and ("tea" in compact or "teatime" in compact):
        return "UK49s Teatime"
    if "uk49" in compact:
        return "UK49s"
    if "lotto" in compact:
        return "Lotto"
    return text


def available_lottery_games(conn: sqlite3.Connection) -> list[str]:
    if not table_exists(conn, "lottery_predictions"):
        return []

    columns = table_columns(conn, "lottery_predictions")
    game_col = first_existing(columns, ["GameName", "Game", "DrawType", "GameGroup"])
    if not game_col:
        return []

    rows = fetch_rows(
        conn,
        f"""
        SELECT DISTINCT {game_col} AS GameName
        FROM lottery_predictions
        WHERE {game_col} IS NOT NULL
        """,
    )

    found = []
    for row in rows:
        name = normalize_game_name(row.get("GameName"))
        if name and name not in found:
            found.append(name)

    ordered = [game for game in GAME_PRIORITY if game in found]
    ordered.extend([game for game in found if game not in ordered])
    return ordered


def game_filter_sql(game_col: str, game_name: str, *, main_result_only: bool = False) -> tuple[str, tuple[Any, ...]]:
    """Return a safe WHERE fragment and params for the selected game.

    main_result_only=True is used for yesterday's result so the WhatsApp post
    stays clean and does not list Lotto Plus / PowerBall Plus alongside the main
    game result.
    """
    game = game_name.lower()

    if game == "daily lotto":
        return f"LOWER({game_col}) LIKE ?", ("%daily%lotto%",)

    if game == "lotto":
        if main_result_only:
            return (
                f"LOWER({game_col}) LIKE ? AND LOWER({game_col}) NOT LIKE ? AND LOWER({game_col}) NOT LIKE ?",
                ("%lotto%", "%daily%", "%plus%"),
            )
        return f"LOWER({game_col}) LIKE ? AND LOWER({game_col}) NOT LIKE ?", ("%lotto%", "%daily%")

    if game == "powerball":
        if main_result_only:
            return f"LOWER({game_col}) LIKE ? AND LOWER({game_col}) NOT LIKE ?", ("%power%", "%plus%")
        return f"LOWER({game_col}) LIKE ?", ("%power%",)

    if game == "uk49s lunchtime":
        return f"LOWER({game_col}) LIKE ? AND LOWER({game_col}) LIKE ?", ("%uk49%", "%lunch%")

    if game == "uk49s teatime":
        return f"LOWER({game_col}) LIKE ? AND (LOWER({game_col}) LIKE ? OR LOWER({game_col}) LIKE ?)", (
            "%uk49%",
            "%tea%",
            "%teatime%",
        )

    return f"LOWER({game_col}) LIKE ?", (f"%{game}%",)


def extract_numbers_from_row(row: dict[str, Any], columns: list[str]) -> list[int]:
    """Extract regular numbers, excluding bonus/powerball columns."""
    numbers: list[int] = []

    number_cols = sorted(
        [col for col in columns if re.fullmatch(r"N\d+", col, flags=re.IGNORECASE)],
        key=lambda col: int(re.search(r"\d+", col).group()),
    )

    if not number_cols:
        number_cols = sorted(
            [
                col
                for col in columns
                if re.fullmatch(r"(Number|Ball|DrawNumber|RegularNumber)\d+", col, flags=re.IGNORECASE)
            ],
            key=lambda col: int(re.search(r"\d+", col).group()),
        )

    for col in number_cols:
        try:
            value = row.get(col)
            if value is not None and str(value).strip() != "":
                numbers.append(int(float(value)))
        except (TypeError, ValueError):
            pass

    if not numbers:
        for col in ["PredictedNumbers", "Numbers", "PredictionNumbers", "ResultNumbers", "WinningNumbers"]:
            text = row.get(col)
            if text:
                for part in re.findall(r"\d+", str(text)):
                    numbers.append(int(part))

    return numbers


def extract_bonus_from_row(row: dict[str, Any], columns: list[str]) -> int | None:
    bonus_col = first_existing(
        columns,
        [
            "Bonus",
            "BonusBall",
            "BonusNumber",
            "PowerBall",
            "Powerball",
            "PowerBallNumber",
            "PB",
        ],
    )
    if not bonus_col:
        return None

    try:
        value = row.get(bonus_col)
        if value is None or str(value).strip() == "":
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def lottery_hot_numbers(conn: sqlite3.Connection, game_name: str, limit_rows: int = 80) -> dict[str, Any]:
    if not table_exists(conn, "lottery_predictions"):
        return {"game": game_name, "numbers": [], "ticket_count": 0}

    columns = table_columns(conn, "lottery_predictions")
    game_col = first_existing(columns, ["GameName", "Game", "DrawType", "GameGroup"])
    if not game_col:
        return {"game": game_name, "numbers": [], "ticket_count": 0}

    where, params = game_filter_sql(game_col, game_name)

    order_terms = []
    if "GeneratedAt" in columns:
        order_terms.append("datetime(GeneratedAt) DESC")
    if "EnsembleGeneratedAt" in columns:
        order_terms.append("datetime(EnsembleGeneratedAt) DESC")
    if "PredictionRank" in columns:
        order_terms.append("PredictionRank ASC")
    order_sql = ", ".join(order_terms) if order_terms else "rowid DESC"

    rows = fetch_rows(
        conn,
        f"""
        SELECT *
        FROM lottery_predictions
        WHERE {where}
        ORDER BY {order_sql}
        LIMIT {int(limit_rows)}
        """,
        params,
    )

    counter: Counter[int] = Counter()
    usable_rows = 0
    for row in rows:
        nums = extract_numbers_from_row(row, columns)
        if nums:
            usable_rows += 1
            counter.update(nums)

    top_three = [num for num, _ in counter.most_common(3)]
    return {"game": game_name, "numbers": top_three, "ticket_count": usable_rows}


def display_game_name(raw: Any) -> str:
    """Return a clean public game name while keeping Plus games distinct."""
    text = safe_str(raw, "").strip()
    if not text:
        return "Lottery"

    compact = re.sub(r"\s+", " ", text).strip().lower()

    if "daily" in compact and "lotto" in compact:
        return "Daily Lotto"
    if "lotto" in compact and "plus" in compact and "2" in compact:
        return "Lotto Plus 2"
    if "lotto" in compact and "plus" in compact and "1" in compact:
        return "Lotto Plus 1"
    if "power" in compact and "plus" in compact:
        return "PowerBall Plus"
    if "power" in compact:
        return "PowerBall"
    if "uk49" in compact and "lunch" in compact:
        return "UK49s Lunchtime"
    if "uk49" in compact and ("tea" in compact or "teatime" in compact):
        return "UK49s Teatime"
    if "uk49" in compact:
        return "UK49s"
    if "lotto" in compact:
        return "Lotto"

    return text


def result_game_sort_key(game_name: str) -> tuple[int, str]:
    priority = [
        "Daily Lotto",
        "Lotto",
        "Lotto Plus 1",
        "Lotto Plus 2",
        "PowerBall",
        "PowerBall Plus",
        "UK49s Lunchtime",
        "UK49s Teatime",
        "UK49s",
    ]
    try:
        return (priority.index(game_name), game_name)
    except ValueError:
        return (999, game_name)


def previous_day_results(conn: sqlite3.Connection, day: dt.date) -> list[dict[str, Any]]:
    """Return all previous-day lottery results that exist in lottery_history."""
    if not table_exists(conn, "lottery_history"):
        return []

    columns = table_columns(conn, "lottery_history")
    date_col = first_existing(columns, ["DrawDate", "ResultDate", "Date"])
    game_col = first_existing(columns, ["GameName", "Game", "DrawType", "GameGroup"])
    if not date_col or not game_col:
        return []

    result_day = day - dt.timedelta(days=1)

    rows = fetch_rows(
        conn,
        f"""
        SELECT *
        FROM lottery_history
        WHERE date({date_col}) = date(?)
        ORDER BY rowid DESC
        """,
        (result_day.isoformat(),),
    )

    results_by_game: dict[str, dict[str, Any]] = {}
    for row in rows:
        game = display_game_name(row.get(game_col))
        numbers = extract_numbers_from_row(row, columns)
        bonus = extract_bonus_from_row(row, columns)

        if not numbers and bonus is None:
            continue

        # Keep one clean line per game for the channel update.
        if game not in results_by_game:
            results_by_game[game] = {
                "game": game,
                "date": result_day,
                "numbers": numbers,
                "bonus": bonus,
            }

    return sorted(results_by_game.values(), key=lambda item: result_game_sort_key(item["game"]))

def choose_game_for_day(conn: sqlite3.Connection, day: dt.date) -> str:
    games = available_lottery_games(conn) or GAME_PRIORITY[:]
    start = week_start_monday(day)
    rng = random.Random(start.isoformat())
    games = games[:]
    rng.shuffle(games)
    return games[(day - start).days % len(games)]


def format_numbers(numbers: list[int]) -> str:
    if not numbers:
        return "Not available yet"
    return " • ".join(f"{num:02d}" for num in numbers)


def format_result_numbers(result: dict[str, Any] | None) -> str | None:
    if not result:
        return None

    numbers_text = format_numbers(result.get("numbers") or [])
    bonus = result.get("bonus")
    if bonus is not None:
        game = safe_str(result.get("game"), "")
        label = "PB" if "power" in game.lower() else "Bonus"
        numbers_text = f"{numbers_text} | {label}: {int(bonus):02d}"
    return numbers_text


def format_results_block(results: list[dict[str, Any]]) -> str:
    if not results:
        return "🎲 Yesterday’s results: Not available yet"

    lines = ["🎲 Yesterday’s results"]
    for result in results:
        game = safe_str(result.get("game"), "Lottery")
        result_text = format_result_numbers(result)
        if result_text:
            lines.append(f"{game}: {result_text}")

    return "\n".join(lines)


def format_lottery_focus_block(hot: dict[str, Any]) -> str:
    game = hot.get("game") or "Lotto"
    numbers = format_numbers(hot.get("numbers") or [])

    return f"🎟️ Number focus: {game}\nHot Picks: {numbers}"

# -----------------------------------------------------------------------------
# Post builders
# -----------------------------------------------------------------------------

def build_daily_post(conn: sqlite3.Connection, day: dt.date, site_url: str) -> str:
    football = best_football_pick(conn, day)
    game = choose_game_for_day(conn, day)
    hot = lottery_hot_numbers(conn, game)
    results = previous_day_results(conn, day)

    return f"""🎯 HexaGrandBet Daily Update
{day.strftime('%A, %d %b %Y')}

{format_results_block(results)}

{format_football_block(football)}

{format_lottery_focus_block(hot)}

View: {site_url}

{DISCLAIMER}
""".strip() + "\n"


def build_weekly_plan(conn: sqlite3.Connection, day: dt.date, site_url: str) -> str:
    start = week_start_monday(day)
    posts = []
    for offset in range(7):
        post_day = start + dt.timedelta(days=offset)
        posts.append(build_daily_post(conn, post_day, site_url))

    divider = "\n\n" + "=" * 52 + "\n\n"
    header = (
        f"HexaGrandBet WhatsApp Channel Weekly Plan\n"
        f"Week starting: {start.isoformat()}\n\n"
        "Copy one short post per day into the WhatsApp Channel.\n"
    )
    return header + divider.join(posts) + "\n"


def fallback_post(day: dt.date, site_url: str) -> str:
    return f"""🎯 HexaGrandBet Daily Update
{day.strftime('%A, %d %b %Y')}

Dashboard refreshed.

View: {site_url}

{DISCLAIMER}
""".strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate HexaGrandBet WhatsApp Channel posts.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output folder for social post text files.")
    parser.add_argument("--site-url", default=DEFAULT_SITE_URL, help="Public HexaGrandBet URL.")
    parser.add_argument("--print", dest="print_post", action="store_true", help="Print the daily post after generating it.")
    args = parser.parse_args()

    db_path = Path(args.db)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    day = today_local()

    if not db_path.exists():
        fallback = fallback_post(day, args.site_url)
        (out_dir / "whatsapp_channel_today.txt").write_text(fallback, encoding=TEXT_ENCODING)
        (out_dir / "whatsapp_channel_weekly_plan.txt").write_text(fallback, encoding=TEXT_ENCODING)
        print(f"Database not found: {db_path}")
        print(f"Wrote fallback WhatsApp post to {out_dir}")
        return 0

    with sqlite3.connect(db_path) as conn:
        today_post = build_daily_post(conn, day, args.site_url)
        weekly_plan = build_weekly_plan(conn, day, args.site_url)

    today_path = out_dir / "whatsapp_channel_today.txt"
    weekly_path = out_dir / "whatsapp_channel_weekly_plan.txt"

    today_path.write_text(today_post, encoding=TEXT_ENCODING)
    weekly_path.write_text(weekly_plan, encoding=TEXT_ENCODING)

    print("Generated WhatsApp Channel content:")
    print(f"- {today_path}")
    print(f"- {weekly_path}")

    if args.print_post:
        print()
        print(today_post)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
