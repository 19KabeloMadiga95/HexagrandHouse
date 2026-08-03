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

GAME_PRIORITY = [
    "Daily Lotto",
    "Lotto",
    "PowerBall",
    "UK49s Lunchtime",
    "UK49s Teatime",
]

DISCLAIMER = "18+ | Analytics only | No guarantees"


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


def clean_date(value: Any) -> str:
    text = safe_str(value, "")
    if not text:
        return ""
    # Keep the date portion if stored as yyyy-mm-dd hh:mm:ss.
    return text[:10]


def today_local() -> dt.date:
    # GitHub Actions runs in UTC. South Africa is UTC+2 and has no DST.
    return (dt.datetime.utcnow() + dt.timedelta(hours=2)).date()


def week_start_monday(day: dt.date) -> dt.date:
    return day - dt.timedelta(days=day.weekday())


def first_existing(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    lookup = {col.lower(): col for col in columns}
    for candidate in candidates:
        found = lookup.get(candidate.lower())
        if found:
            return found
    return None


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


def game_filter_sql(game_col: str, game_name: str) -> tuple[str, tuple[Any, ...]]:
    game = game_name.lower()
    if game == "daily lotto":
        return f"LOWER({game_col}) LIKE ?", ("%daily%lotto%",)
    if game == "lotto":
        return f"LOWER({game_col}) LIKE ? AND LOWER({game_col}) NOT LIKE ?", ("%lotto%", "%daily%")
    if game == "powerball":
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
    numbers: list[int] = []

    # Preferred modern structure: N1, N2, ..., N6. Bonus is deliberately ignored
    # for the hot regular-number list.
    number_cols = sorted(
        [col for col in columns if re.fullmatch(r"N\d+", col, flags=re.IGNORECASE)],
        key=lambda col: int(re.search(r"\d+", col).group()),
    )
    for col in number_cols:
        try:
            value = row.get(col)
            if value is not None and str(value).strip() != "":
                numbers.append(int(float(value)))
        except (TypeError, ValueError):
            pass

    # Older/backtest structure: PredictedNumbers = "1,2,3,4,5".
    if not numbers:
        for col in ["PredictedNumbers", "Numbers", "PredictionNumbers"]:
            text = row.get(col)
            if text:
                for part in re.findall(r"\d+", str(text)):
                    numbers.append(int(part))

    return numbers


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


def choose_game_for_day(conn: sqlite3.Connection, day: dt.date) -> str:
    games = available_lottery_games(conn) or GAME_PRIORITY[:]
    start = week_start_monday(day)
    rng = random.Random(start.isoformat())
    games = games[:]
    rng.shuffle(games)
    return games[(day - start).days % len(games)]


def format_hot_numbers(numbers: list[int]) -> str:
    if not numbers:
        return "Not available yet"
    return " • ".join(f"{num:02d}" for num in numbers)


def format_football_block(pick: dict[str, Any] | None) -> str:
    if not pick:
        return "⚽ Best football pick: No strong current fixture pick available today."

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

    lines = [
        "⚽ Best football pick",
        f"{home} vs {away}",
        f"League: {league}",
        f"Pick: {signal}",
        f"Strength: {confidence} ({probability})",
    ]
    if kickoff:
        lines.insert(3, f"Kickoff: {kickoff}")
    return "\n".join(lines)


def build_daily_post(conn: sqlite3.Connection, day: dt.date, site_url: str) -> str:
    football = best_football_pick(conn, day)
    game = choose_game_for_day(conn, day)
    hot = lottery_hot_numbers(conn, game)

    generated = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"""🎯 HexaGrandBet Daily Pick Card
{day.strftime('%A, %d %b %Y')}

{format_football_block(football)}

🎟️ Lotto hot numbers
Game: {hot['game']}
Hot 3: {format_hot_numbers(hot['numbers'])}
Based on: current predicted ticket lineups

View the dashboard:
{site_url}

{DISCLAIMER}
Generated: {generated}
""".strip() + "\n"


def build_weekly_plan(conn: sqlite3.Connection, day: dt.date, site_url: str) -> str:
    start = week_start_monday(day)
    posts = []
    for offset in range(7):
        post_day = start + dt.timedelta(days=offset)
        posts.append(build_daily_post(conn, post_day, site_url))

    divider = "\n\n" + "=" * 58 + "\n\n"
    header = f"HexaGrandBet WhatsApp Channel Weekly Plan\nWeek starting: {start.isoformat()}\n\nCopy one post per day into the WhatsApp Channel.\n"
    return header + divider.join(posts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate HexaGrandBet WhatsApp Channel posts.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output folder for social post text files.")
    parser.add_argument("--site-url", default=DEFAULT_SITE_URL, help="Public HexaGrandBet URL.")
    args = parser.parse_args()

    db_path = Path(args.db)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    day = today_local()

    if not db_path.exists():
        fallback = f"""🎯 HexaGrandBet Daily Update
{day.strftime('%A, %d %b %Y')}

Dashboard refresh completed, but the local database was not found for post generation.

View the dashboard:
{args.site_url}

{DISCLAIMER}
""".strip() + "\n"
        (out_dir / "whatsapp_channel_today.txt").write_text(fallback, encoding="utf-8")
        (out_dir / "whatsapp_channel_weekly_plan.txt").write_text(fallback, encoding="utf-8")
        print(f"Database not found: {db_path}")
        print(f"Wrote fallback WhatsApp post to {out_dir}")
        return 0

    with sqlite3.connect(db_path) as conn:
        today_post = build_daily_post(conn, day, args.site_url)
        weekly_plan = build_weekly_plan(conn, day, args.site_url)

    today_path = out_dir / "whatsapp_channel_today.txt"
    weekly_path = out_dir / "whatsapp_channel_weekly_plan.txt"

    today_path.write_text(today_post, encoding="utf-8")
    weekly_path.write_text(weekly_plan, encoding="utf-8")

    print("Generated WhatsApp Channel content:")
    print(f"- {today_path}")
    print(f"- {weekly_path}")
    print()
    print(today_post)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
