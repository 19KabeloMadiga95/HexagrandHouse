from __future__ import annotations

import pandas as pd


def build_summary_from_history(history_df: pd.DataFrame) -> pd.DataFrame:
    if history_df.empty:
        return pd.DataFrame()

    rows = []

    metrics = [
        ("Result Accuracy", "ResultHit"),
        ("Goals Accuracy", "GoalsHit"),
        ("Corners Accuracy", "CornersHit"),
    ]

    for metric_name, col in metrics:
        if col in history_df.columns:
            rate = pd.to_numeric(
                history_df[col],
                errors="coerce",
            ).mean()

            rows.append(
                {
                    "Metric": metric_name,
                    "HitRatePct": round(rate * 100, 1),
                    "FixturesScored": int(
                        pd.to_numeric(
                            history_df[col],
                            errors="coerce",
                        ).count()
                    ),
                }
            )

    return pd.DataFrame(rows)


def build_group_summary(
    history_df: pd.DataFrame,
    group_column: str,
) -> pd.DataFrame:
    if history_df.empty or group_column not in history_df.columns:
        return pd.DataFrame()

    rows = []

    grouped = history_df.groupby(
        group_column,
        dropna=False,
    )

    for group_value, group in grouped:
        row = {
            group_column: group_value,
            "FixturesScored": len(group),
        }

        for metric_name, col in [
            ("ResultHitRate", "ResultHit"),
            ("GoalsHitRate", "GoalsHit"),
            ("CornersHitRate", "CornersHit"),
        ]:
            if col in group.columns:
                row[metric_name] = pd.to_numeric(
                    group[col],
                    errors="coerce",
                ).mean()

        rows.append(row)

    return pd.DataFrame(rows)


def convert_rate_columns_to_percent(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    rate_cols = [
        "ResultHitRate",
        "GoalsHitRate",
        "CornersHitRate",
        "ResultAccuracy",
        "GoalsAccuracy",
        "CornersAccuracy",
    ]

    for col in rate_cols:
        if col in df.columns:
            df[col] = (
                pd.to_numeric(
                    df[col],
                    errors="coerce",
                ) * 100
            ).round(1)

    return df