import sqlite3
from pathlib import Path

SOURCE_DB = Path("data/hexagrandhouse.db")
RUNTIME_DB = Path("data/hexagrandhouse_cloud_runtime.db")

FULL_COPY_TABLES = [
    # Core runtime history
    "lottery_history",
    "football_history",

    # Lottery feature tables are small enough for runtime
    "lottery_base_features",
    "lottery_powerball_features",
    "lottery_lotto_features",
    "lottery_daily_lotto_features",
    "lottery_uk49s_features",

    # Lottery predictions
    "lottery_predictions",
    "lottery_ensemble_predictions",
    "lottery_powerball_predictions",
    "lottery_lotto_predictions",
    "lottery_daily_lotto_predictions",
    "lottery_uk49s_predictions",

    # Lottery reporting
    "lottery_daily_best_models",
    "lottery_daily_latest_results",
    "lottery_daily_quality_snapshot",
    "lottery_daily_quick_insights",
    "lottery_daily_summary_snapshot",
    "lottery_daily_top_predictions",
    "lottery_executive_coverage_summary",
    "lottery_executive_latest_results",
    "lottery_executive_platform_status",
    "lottery_executive_statistical_insights",
    "lottery_executive_summary",
    "lottery_executive_top_signals",
    "lottery_model_best_by_game",
    "lottery_model_dashboard_summary",
    "lottery_model_game_summary",
    "lottery_model_leaderboard",
    "lottery_model_notes",
    "lottery_model_vs_random",
    "lottery_powerball_model_dashboard_summary",
    "lottery_powerball_model_leaderboard",
    "lottery_powerball_model_notes",
    "lottery_powerball_model_vs_random",

    # Football small/reporting/runtime tables
    "football_fixtures",
    "football_feature_summary",
    "football_feature_dictionary",
    "football_model_summary",
    "football_file_status",
    "football_grade_summary",
    "football_league_performance",
    "football_market_performance",
    "football_performance_dashboard_summary",
    "football_performance_kpis",
    "football_performance_notes",
    "football_top_plays",
    "football_top_plays_by_league",
    "football_top_plays_by_market",
    "football_top_plays_by_rating",
    "football_top_plays_notes",
    "football_top_plays_summary",
    "football_value_bets",
    "football_value_bet_details",
    "football_value_bet_notes",
    "football_value_bet_summary",
    "football_value_bets_by_league",
    "football_value_bets_by_rating",

    # Platform
    "platform_refresh_status",
    "platform_run_log",
]

# Heavy development/model tables are kept as limited runtime samples/signals only.
LIMITED_TABLES = {
    "football_predictions": 5000,
    "football_ensemble_predictions": 5000,
    "football_backtest_history": 5000,
    "football_result_model_predictions": 1000,
    "football_goals_model_predictions": 1000,
    "football_corners_model_predictions": 1000,
    "football_match_features": 1000,
    "football_team_features": 1000,
    "football_team_match_long": 1000,
    "football_match_features_tier1": 1000,
    "football_match_features_tier2": 1000,
    "football_match_features_tier3": 1000,
}

ORDER_PREFERENCE = [
    "ConfidenceScore",
    "confidence_score",
    "SignalScore",
    "ModelScore",
    "Score",
    "RatingScore",
    "EdgeScore",
    "MatchDate",
    "FixtureDate",
    "GeneratedAt",
    "PredictionDate",
    "Date",
]


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM main.sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def get_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({quote_identifier(table_name)})").fetchall()]


def count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM main.{quote_identifier(table_name)}").fetchone()[0]


def order_clause(columns: list[str]) -> str:
    selected = [col for col in ORDER_PREFERENCE if col in columns]

    if not selected:
        return ""

    parts = [f"{quote_identifier(col)} DESC" for col in selected[:3]]
    return " ORDER BY " + ", ".join(parts)


def copy_full(conn: sqlite3.Connection, table_name: str) -> int:
    q = quote_identifier(table_name)
    conn.execute(f"DROP TABLE IF EXISTS runtime.{q}")
    conn.execute(f"CREATE TABLE runtime.{q} AS SELECT * FROM main.{q}")
    return conn.execute(f"SELECT COUNT(*) FROM runtime.{q}").fetchone()[0]


def copy_limited(conn: sqlite3.Connection, table_name: str, limit: int) -> int:
    q = quote_identifier(table_name)
    columns = get_columns(conn, table_name)
    order_sql = order_clause(columns)

    conn.execute(f"DROP TABLE IF EXISTS runtime.{q}")
    conn.execute(
        f"CREATE TABLE runtime.{q} AS "
        f"SELECT * FROM main.{q}{order_sql} LIMIT {int(limit)}"
    )
    return conn.execute(f"SELECT COUNT(*) FROM runtime.{q}").fetchone()[0]


def main() -> None:
    if not SOURCE_DB.exists():
        raise FileNotFoundError(f"Source database not found: {SOURCE_DB}")

    if RUNTIME_DB.exists():
        RUNTIME_DB.unlink()

    source_size = SOURCE_DB.stat().st_size / 1024 / 1024

    print("Building cloud-safe runtime database...")
    print(f"Source : {SOURCE_DB}")
    print(f"Source size: {source_size:.2f} MB")
    print(f"Output : {RUNTIME_DB}")
    print()

    conn = sqlite3.connect(SOURCE_DB)
    conn.execute("ATTACH DATABASE ? AS runtime", (str(RUNTIME_DB.resolve()),))

    copied_total = 0

    for table in FULL_COPY_TABLES:
        if not table_exists(conn, table):
            print(f"SKIP missing   {table}")
            continue

        rows = copy_full(conn, table)
        copied_total += rows
        print(f"COPIED full    {table}: {rows}")

    for table, limit in LIMITED_TABLES.items():
        if not table_exists(conn, table):
            print(f"SKIP missing   {table}")
            continue

        rows = copy_limited(conn, table, limit)
        copied_total += rows
        print(f"COPIED limited {table}: {rows}")

    conn.commit()
    conn.execute("DETACH DATABASE runtime")
    conn.close()

    # Vacuum runtime DB in its own connection.
    runtime_conn = sqlite3.connect(RUNTIME_DB)
    runtime_conn.execute("VACUUM")
    runtime_conn.close()

    runtime_size = RUNTIME_DB.stat().st_size / 1024 / 1024

    print()
    print("Runtime DB created:")
    print(RUNTIME_DB)
    print(f"Size: {runtime_size:.2f} MB")
    print(f"Total copied rows: {copied_total}")


if __name__ == "__main__":
    main()
