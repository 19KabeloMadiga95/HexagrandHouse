from __future__ import annotations

import argparse
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

DB = Path("data/hexagrandhouse.db")


def _latest(conn: sqlite3.Connection, table: str, date_col: str):
    try:
        row = conn.execute(f'SELECT MAX({date_col}) FROM "{table}"').fetchone()
    except sqlite3.Error:
        return None
    return row[0] if row else None


def _count(conn: sqlite3.Connection, table: str, where: str | None = None) -> int | None:
    try:
        sql = f'SELECT COUNT(*) FROM "{table}"'
        if where:
            sql += f" WHERE {where}"
        return int(conn.execute(sql).fetchone()[0])
    except sqlite3.Error:
        return None


def _lag_days(value) -> int | None:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return (date.today() - parsed.date()).days


def main() -> None:
    parser = argparse.ArgumentParser(description="Check HexagrandHouse runtime data freshness.")
    parser.add_argument("--max-lottery-lag-days", type=int, default=4)
    parser.add_argument("--fail-football-history", action="store_true")
    parser.add_argument("--max-football-lag-days", type=int, default=14)
    parser.add_argument("--require-football-fixtures", action="store_true")
    args = parser.parse_args()

    if not DB.exists():
        raise SystemExit(f"Missing database: {DB}")

    conn = sqlite3.connect(DB)
    lottery_latest = _latest(conn, "lottery_history", "DrawDate")
    football_latest = _latest(conn, "football_history", "MatchDate")
    fixture_latest = _latest(conn, "football_fixtures", "FixtureDate")
    today_text = date.today().strftime("%Y-%m-%d")
    upcoming_fixtures = _count(conn, "football_fixtures", f"date(FixtureDate) >= date('{today_text}')")
    fixture_predictions = _count(conn, "football_fixture_predictions")
    conn.close()

    lottery_lag = _lag_days(lottery_latest)
    football_lag = _lag_days(football_latest)

    print(f"Lottery latest       : {lottery_latest} | lag days: {lottery_lag}")
    print(f"Football history     : {football_latest} | lag days: {football_lag}")
    print(f"Football fixtures max: {fixture_latest}")
    print(f"Upcoming fixtures    : {upcoming_fixtures}")
    print(f"Fixture predictions  : {fixture_predictions}")

    if lottery_lag is None:
        raise SystemExit("Lottery freshness check failed: no valid latest draw date.")

    if lottery_lag > args.max_lottery_lag_days:
        raise SystemExit(
            f"Lottery data is stale: latest draw is {lottery_lag} days old "
            f"(limit {args.max_lottery_lag_days})."
        )

    if args.fail_football_history:
        if football_lag is None:
            raise SystemExit("Football freshness check failed: no valid latest match date.")
        if football_lag > args.max_football_lag_days:
            raise SystemExit(
                f"Football history is stale: latest match is {football_lag} days old "
                f"(limit {args.max_football_lag_days})."
            )

    if args.require_football_fixtures:
        if not upcoming_fixtures or upcoming_fixtures < 1:
            raise SystemExit("Football fixture freshness check failed: no upcoming fixtures loaded.")

    print("Freshness check passed.")


if __name__ == "__main__":
    main()
