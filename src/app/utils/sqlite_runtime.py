from __future__ import annotations

from typing import Iterable

import pandas as pd
import streamlit as st

from src.data.database import (
    get_database_summary,
    list_tables,
    read_table,
)


DATE_COLUMNS = [
    "GeneratedAt",
    "DrawDate",
    "FixtureDate",
    "MatchDate",
    "Date",
    "CreatedAt",
    "LoadedAt",
]


CONFIDENCE_COLUMNS = [
    "ConfidenceScore",
    "EnsembleConfidenceScore",
    "Confidence",
    "Score",
    "EnsembleScore",
]


def available_tables() -> list[str]:
    return list_tables()


def database_summary() -> pd.DataFrame:
    df = get_database_summary()
    if df.empty:
        return pd.DataFrame(columns=["TableName", "RowCount"])
    return df.sort_values("TableName").reset_index(drop=True)


def table_exists(table_name: str) -> bool:
    return table_name in available_tables()


@st.cache_data(show_spinner=False, ttl=300)
def cached_table(table_name: str, limit: int | None = None) -> pd.DataFrame:
    df = read_table(table_name, limit=limit, warn_if_missing=False)
    return clean_dataframe(df)


def clean_dataframe(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()

    for col in out.columns:
        if col in DATE_COLUMNS or col.lower().endswith("date") or col.lower().endswith("at"):
            try:
                parsed = pd.to_datetime(out[col], errors="coerce")
                if parsed.notna().any():
                    out[col] = parsed
            except Exception:
                pass

    return out


def first_existing_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    for column in candidates:
        if column in df.columns:
            return column
    return None


def sort_by_best_date(df: pd.DataFrame, ascending: bool = False) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    column = first_existing_column(out, DATE_COLUMNS)
    if column is None:
        return out

    try:
        return out.sort_values(column, ascending=ascending, na_position="last")
    except Exception:
        return out


def sort_by_confidence(df: pd.DataFrame, ascending: bool = False) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    column = first_existing_column(out, CONFIDENCE_COLUMNS)
    if column is None:
        return out

    try:
        out[column] = pd.to_numeric(out[column], errors="coerce")
        return out.sort_values(column, ascending=ascending, na_position="last")
    except Exception:
        return out


def filter_by_column_value(df: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    if df is None or df.empty or value in (None, "", "All") or column not in df.columns:
        return df
    return df[df[column].astype(str) == str(value)]


def unique_options(df: pd.DataFrame, column: str, include_all: bool = True) -> list[str]:
    if df is None or df.empty or column not in df.columns:
        return ["All"] if include_all else []

    values = (
        df[column]
        .dropna()
        .astype(str)
        .map(str.strip)
    )
    values = sorted(v for v in values.unique().tolist() if v)
    return (["All"] if include_all else []) + values


def count_rows(table_name: str) -> int:
    summary = database_summary()
    if summary.empty:
        return 0
    row = summary[summary["TableName"] == table_name]
    if row.empty:
        return 0
    try:
        return int(row.iloc[0]["RowCount"])
    except Exception:
        return 0


def latest_value(df: pd.DataFrame, column: str, default: str = "-") -> str:
    if df is None or df.empty or column not in df.columns:
        return default

    series = df[column].dropna()
    if series.empty:
        return default

    value = series.iloc[0]
    try:
        if isinstance(value, pd.Timestamp):
            return value.strftime("%Y-%m-%d")
    except Exception:
        pass
    return str(value)


def show_database_download(df: pd.DataFrame, filename: str, label: str = "Download CSV") -> None:
    if df is None or df.empty:
        return

    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )
