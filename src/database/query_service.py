import pandas as pd

from database.database_connection import (
    database_exists,
    run_query,
    read_table,
    table_exists,
    get_database_summary,
)


def get_platform_summary():
    if not database_exists():
        return pd.DataFrame()

    return get_database_summary()


def get_latest_lottery_history(limit=100):
    if not table_exists("lottery_history"):
        return pd.DataFrame()

    query = """
    SELECT *
    FROM lottery_history
    ORDER BY DrawDate DESC
    LIMIT ?
    """

    return run_query(query, [limit])


def get_latest_lottery_predictions(limit=100):
    if not table_exists("lottery_predictions"):
        return pd.DataFrame()

    query = """
    SELECT *
    FROM lottery_predictions
    ORDER BY GeneratedAt DESC
    LIMIT ?
    """

    return run_query(query, [limit])


def get_lottery_predictions_by_game(game_name, limit=50):
    if not table_exists("lottery_predictions"):
        return pd.DataFrame()

    query = """
    SELECT *
    FROM lottery_predictions
    WHERE GameName = ?
       OR GameFamily = ?
       OR DrawType = ?
    ORDER BY GeneratedAt DESC
    LIMIT ?
    """

    return run_query(
        query,
        [
            game_name,
            game_name,
            game_name,
            limit,
        ]
    )


def get_lottery_result_coverage():
    if not table_exists("lottery_history"):
        return pd.DataFrame()

    query = """
    SELECT
        GameFamily,
        GameName,
        DrawType,
        COUNT(*) AS DrawCount,
        MAX(DrawDate) AS LatestDrawDate,
        MIN(DrawDate) AS EarliestDrawDate
    FROM lottery_history
    GROUP BY
        GameFamily,
        GameName,
        DrawType
    ORDER BY DrawCount DESC
    """

    return run_query(query)


def get_recent_lottery_results(days=7, limit=100):
    if not table_exists("lottery_history"):
        return pd.DataFrame()

    query = """
    SELECT *
    FROM lottery_history
    WHERE DATE(DrawDate) >= DATE('now', ?)
    ORDER BY DrawDate DESC
    LIMIT ?
    """

    return run_query(
        query,
        [
            f"-{int(days)} days",
            limit,
        ]
    )


def get_football_history(limit=1000):
    if not table_exists("football_history"):
        return pd.DataFrame()

    query = """
    SELECT *
    FROM football_history
    ORDER BY MatchDate DESC
    LIMIT ?
    """

    return run_query(query, [limit])


def get_recent_football_results(days=7, limit=200):
    if not table_exists("football_history"):
        return pd.DataFrame()

    query = """
    SELECT *
    FROM football_history
    WHERE DATE(MatchDate) >= DATE('now', ?)
      AND HomeGoals IS NOT NULL
      AND AwayGoals IS NOT NULL
    ORDER BY MatchDate DESC
    LIMIT ?
    """

    return run_query(
        query,
        [
            f"-{int(days)} days",
            limit,
        ]
    )


def get_football_league_coverage():
    if not table_exists("football_history"):
        return pd.DataFrame()

    query = """
    SELECT
        League,
        Country,
        COUNT(*) AS MatchCount,
        MAX(MatchDate) AS LatestMatchDate,
        MIN(MatchDate) AS EarliestMatchDate
    FROM football_history
    GROUP BY
        League,
        Country
    ORDER BY MatchCount DESC
    """

    return run_query(query)


def get_football_predictions(limit=200):
    if table_exists("football_predictions"):
        query = """
        SELECT *
        FROM football_predictions
        LIMIT ?
        """

        return run_query(query, [limit])

    if table_exists("football_ensemble_predictions"):
        query = """
        SELECT *
        FROM football_ensemble_predictions
        LIMIT ?
        """

        return run_query(query, [limit])

    return pd.DataFrame()


def get_top_football_predictions(limit=25):
    if table_exists("football_predictions"):
        table_name = "football_predictions"
    elif table_exists("football_ensemble_predictions"):
        table_name = "football_ensemble_predictions"
    else:
        return pd.DataFrame()

    df = read_table(table_name)

    if df.empty:
        return df

    sort_cols = [
        "ElitePrediction",
        "EnsembleConfidenceScore",
        "ValueScore",
        "SignalCount",
    ]

    existing_sort_cols = [
        col for col in sort_cols
        if col in df.columns
    ]

    for col in existing_sort_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    if existing_sort_cols:
        df = df.sort_values(
            by=existing_sort_cols,
            ascending=[False] * len(existing_sort_cols)
        )

    return df.head(limit)


def get_football_backtest_history(limit=500):
    if not table_exists("football_backtest_history"):
        return pd.DataFrame()

    query = """
    SELECT *
    FROM football_backtest_history
    ORDER BY FixtureDate DESC
    LIMIT ?
    """

    return run_query(query, [limit])


def get_model_accuracy_summary():
    if not table_exists("football_backtest_history"):
        return pd.DataFrame()

    query = """
    SELECT
        COUNT(*) AS FixturesScored,
        AVG(ResultHit) * 100 AS ResultAccuracyPct,
        AVG(GoalsHit) * 100 AS GoalsAccuracyPct,
        AVG(CornersHit) * 100 AS CornersAccuracyPct
    FROM football_backtest_history
    """

    return run_query(query)


def get_model_accuracy_by_league():
    if not table_exists("football_backtest_history"):
        return pd.DataFrame()

    query = """
    SELECT
        League,
        COUNT(*) AS FixturesScored,
        AVG(ResultHit) * 100 AS ResultAccuracyPct,
        AVG(GoalsHit) * 100 AS GoalsAccuracyPct,
        AVG(CornersHit) * 100 AS CornersAccuracyPct
    FROM football_backtest_history
    GROUP BY League
    ORDER BY FixturesScored DESC
    """

    return run_query(query)


def get_model_accuracy_by_grade():
    if not table_exists("football_backtest_history"):
        return pd.DataFrame()

    query = """
    SELECT
        BettingGrade,
        COUNT(*) AS FixturesScored,
        AVG(ResultHit) * 100 AS ResultAccuracyPct,
        AVG(GoalsHit) * 100 AS GoalsAccuracyPct,
        AVG(CornersHit) * 100 AS CornersAccuracyPct
    FROM football_backtest_history
    GROUP BY BettingGrade
    ORDER BY FixturesScored DESC
    """

    return run_query(query)


def search_football_team(team_name, limit=100):
    if not table_exists("football_history"):
        return pd.DataFrame()

    query = """
    SELECT *
    FROM football_history
    WHERE HomeTeam LIKE ?
       OR AwayTeam LIKE ?
    ORDER BY MatchDate DESC
    LIMIT ?
    """

    search_value = f"%{team_name}%"

    return run_query(
        query,
        [
            search_value,
            search_value,
            limit,
        ]
    )


def search_lottery_game(game_name, limit=100):
    if not table_exists("lottery_history"):
        return pd.DataFrame()

    query = """
    SELECT *
    FROM lottery_history
    WHERE GameName LIKE ?
       OR GameFamily LIKE ?
       OR DrawType LIKE ?
    ORDER BY DrawDate DESC
    LIMIT ?
    """

    search_value = f"%{game_name}%"

    return run_query(
        query,
        [
            search_value,
            search_value,
            search_value,
            limit,
        ]
    )