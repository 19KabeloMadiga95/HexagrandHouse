from __future__ import annotations

import html
import pandas as pd


def clean_text(value, default: str = "") -> str:
    if value is None or pd.isna(value):
        return default

    value = str(value).strip()

    if value.lower() in {"nan", "none", "nat", ""}:
        return default

    return value


def safe_text(value, default: str = "-") -> str:
    value = clean_text(value, default)

    if value == default:
        return default

    return html.escape(value)


def safe_number(value, default="-"):
    if value is None or pd.isna(value):
        return default

    try:
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default=0.0) -> float:
    if value is None or pd.isna(value):
        return default

    try:
        return float(value)
    except Exception:
        return default


def format_date(value, fmt: str = "%A • %d %b %Y") -> str:
    try:
        value = pd.to_datetime(value, errors="coerce")

        if pd.isna(value):
            return "-"

        return value.strftime(fmt)
    except Exception:
        return "-"


def format_short_date(value) -> str:
    return format_date(value, "%Y-%m-%d")


def format_currency(value, prefix: str = "R") -> str:
    if value is None or pd.isna(value):
        return "-"

    try:
        value = float(value)

        if value >= 1_000_000:
            return f"{prefix}{round(value / 1_000_000, 1)}M"

        if value >= 1_000:
            return f"{prefix}{round(value / 1_000, 1)}K"

        return f"{prefix}{round(value, 2)}"
    except Exception:
        return safe_text(value)


def format_percent(value, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"

    try:
        return f"{round(float(value), decimals)}%"
    except Exception:
        return "-"


def format_confidence(value) -> str:
    try:
        value = float(value)
    except Exception:
        return "Unrated"

    if value >= 85:
        return "Elite"
    if value >= 75:
        return "High"
    if value >= 60:
        return "Medium"
    if value > 0:
        return "Low"

    return "Unrated"


def format_odds(value) -> str:
    if value is None or pd.isna(value):
        return "-"

    try:
        return f"{float(value):.2f}"
    except Exception:
        return "-"