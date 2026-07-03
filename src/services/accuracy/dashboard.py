from __future__ import annotations

from src.services.accuracy.history import load_accuracy_history
from src.services.accuracy.statistics import build_kpis
from src.services.accuracy.summaries import (
    build_summary_from_history,
    build_group_summary,
    convert_rate_columns_to_percent,
)
from src.services.accuracy.charts import (
    build_accuracy_trend,
    get_sort_column,
)


def get_accuracy_dashboard_data() -> dict:
    history_df = load_accuracy_history()

    summary_df = build_summary_from_history(history_df)

    league_df = build_group_summary(
        history_df,
        "League",
    )

    grade_df = build_group_summary(
        history_df,
        "BettingGrade",
    )

    league_display_df = convert_rate_columns_to_percent(league_df)
    grade_display_df = convert_rate_columns_to_percent(grade_df)

    league_sort_col = get_sort_column(league_display_df)
    grade_sort_col = get_sort_column(grade_display_df)

    if league_sort_col:
        league_display_df = league_display_df.sort_values(
            by=league_sort_col,
            ascending=False,
        )

    if grade_sort_col:
        grade_display_df = grade_display_df.sort_values(
            by=grade_sort_col,
            ascending=False,
        )

    return {
        "history_df": history_df,
        "summary_df": summary_df,
        "league_df": league_display_df,
        "grade_df": grade_display_df,
        "trend_df": build_accuracy_trend(history_df),
        "kpis": build_kpis(history_df),
        "sort_columns": {
            "league": league_sort_col,
            "grade": grade_sort_col,
        },
    }