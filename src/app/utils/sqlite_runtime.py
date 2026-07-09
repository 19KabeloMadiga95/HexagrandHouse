from __future__ import annotations

from typing import Iterable
import pandas as pd
import streamlit as st

from src.data.database import get_database_summary, list_tables, read_table


DATE_COLUMNS = [
    "GeneratedAt", "EnsembleGeneratedAt", "DrawDate", "FixtureDate",
    "MatchDate", "Date", "CreatedAt", "LoadedAt", "UpdatedAt",
]

CONFIDENCE_COLUMNS = [
    "ConfidenceScore", "EnsembleConfidenceScore", "Confidence", "Score",
    "RawScore", "EnsembleScore", "PickScore",
]


def available_tables() -> list[str]:
    try:
        return list_tables()
    except Exception:
        return []


def table_exists(table_name: str) -> bool:
    return table_name in available_tables()


def database_summary() -> pd.DataFrame:
    try:
        df = get_database_summary()
    except Exception:
        return pd.DataFrame(columns=["TableName", "RowCount"])
    if df is None or df.empty:
        return pd.DataFrame(columns=["TableName", "RowCount"])
    return df.sort_values("TableName").reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=300)
def cached_table(table_name: str, limit: int | None = None) -> pd.DataFrame:
    try:
        df = read_table(table_name, limit=limit, warn_if_missing=False)
    except TypeError:
        try:
            df = read_table(table_name, limit=limit)
        except Exception:
            df = pd.DataFrame()
    except Exception:
        df = pd.DataFrame()
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


def first_existing_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def sort_by_date(df: pd.DataFrame, ascending: bool = False) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    col = first_existing_column(out, DATE_COLUMNS)
    if not col:
        return out
    try:
        return out.sort_values(col, ascending=ascending, na_position="last")
    except Exception:
        return out


def sort_by_strength(df: pd.DataFrame, ascending: bool = False) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    col = first_existing_column(out, CONFIDENCE_COLUMNS)
    if not col:
        return out
    try:
        out[col] = pd.to_numeric(out[col], errors="coerce")
        return out.sort_values(col, ascending=ascending, na_position="last")
    except Exception:
        return out


def unique_options(df: pd.DataFrame, column: str, include_all: bool = True) -> list[str]:
    if df is None or df.empty or column not in df.columns:
        return ["All"] if include_all else []
    values = df[column].dropna().astype(str).map(str.strip)
    values = sorted(v for v in values.unique().tolist() if v and v.lower() not in {"nan", "none"})
    return (["All"] if include_all else []) + values


def filter_value(df: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    if df is None or df.empty or value in (None, "", "All") or column not in df.columns:
        return df
    return df[df[column].astype(str) == str(value)]


def format_date(value, default: str = "-") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    try:
        value = pd.to_datetime(value, errors="coerce")
        if pd.notna(value):
            return value.strftime("%d %b %Y")
    except Exception:
        pass
    text = str(value)
    return text if text else default


def latest_label(df: pd.DataFrame, date_col: str = "DrawDate", game_col: str = "GameName") -> str:
    if df is None or df.empty:
        return "-"
    out = sort_by_date(df)
    if out.empty:
        return "-"
    row = out.iloc[0]
    game = row.get(game_col, row.get("GameFamily", "Latest"))
    date = format_date(row.get(date_col, row.get("Date", None)))
    return f"{game} • {date}"


def safe_int(value, default: int = 0) -> int:
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default

# Compatibility helpers used by backstage/admin pages.
def sort_by_best_date(df: pd.DataFrame, ascending: bool = False) -> pd.DataFrame:
    return sort_by_date(df, ascending=ascending)


def sort_by_confidence(df: pd.DataFrame, ascending: bool = False) -> pd.DataFrame:
    return sort_by_strength(df, ascending=ascending)


def filter_by_column_value(df: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    return filter_value(df, column, value)


def latest_value(df: pd.DataFrame, date_col: str = "Date") -> str:
    if df is None or df.empty:
        return "-"
    out = sort_by_date(df)
    if out.empty:
        return "-"
    row = out.iloc[0]
    return format_date(row.get(date_col, None))


def show_database_download(df: pd.DataFrame, filename: str = "data.csv") -> None:
    if df is None or df.empty:
        return
    try:
        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name=filename,
            mime="text/csv",
            use_container_width=True,
        )
    except Exception:
        pass
