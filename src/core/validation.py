import pandas as pd

from src.core.logging import warning, success


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str = "Dataset",
) -> bool:
    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        warning(
            f"{dataset_name} missing required columns: {missing}"
        )
        return False

    success(
        f"{dataset_name} contains all required columns."
    )
    return True


def get_missing_columns(
    df: pd.DataFrame,
    required_columns: list[str],
) -> list[str]:
    return [
        col for col in required_columns
        if col not in df.columns
    ]


def add_missing_columns(
    df: pd.DataFrame,
    columns: list[str],
    default_value=None,
) -> pd.DataFrame:
    df = df.copy()

    for col in columns:
        if col not in df.columns:
            df[col] = default_value

    return df


def validate_non_empty(
    df: pd.DataFrame,
    dataset_name: str = "Dataset",
) -> bool:
    if df.empty:
        warning(f"{dataset_name} is empty.")
        return False

    success(f"{dataset_name} rows: {len(df)}")
    return True