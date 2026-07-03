from __future__ import annotations

import pandas as pd


def first_existing_column(
    df: pd.DataFrame,
    possible_columns: list[str],
):
    for col in possible_columns:
        if col in df.columns:
            return col

    return None


def safe_numeric(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

    return df


def safe_datetime(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce",
            )

    return df


def sort_if_exists(
    df: pd.DataFrame,
    column: str,
    ascending: bool = True,
) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return df

    return df.sort_values(
        by=column,
        ascending=ascending,
    )


def filter_equals(
    df: pd.DataFrame,
    column: str,
    value,
) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return df

    return df[
        df[column].astype(str) == str(value)
    ].copy()


def value_counts_df(
    df: pd.DataFrame,
    column: str,
    value_name: str = "Count",
    label_name: str = "Label",
) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return pd.DataFrame()

    result = (
        df[column]
        .value_counts()
        .reset_index()
    )

    result.columns = [label_name, value_name]

    return result


def select_existing_columns(
    df: pd.DataFrame,
    columns: list[str],
) -> list[str]:
    return [
        col for col in columns
        if col in df.columns
    ]