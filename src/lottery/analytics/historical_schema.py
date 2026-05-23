from pathlib import Path
from datetime import datetime

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

DATA_DIR = BASE_DIR / "data"
MASTER_DIR = DATA_DIR / "master"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"

MASTER_FILE = MASTER_DIR / "lottery_historical_master.xlsx"


# =========================================================
# STANDARD HISTORICAL LOTTERY SCHEMA
# =========================================================

HISTORICAL_COLUMNS = [
    "GameFamily",
    "GameName",
    "DrawType",
    "DrawNumber",
    "DrawDate",
    "DrawDay",
    "N1",
    "N2",
    "N3",
    "N4",
    "N5",
    "N6",
    "Bonus",
    "Jackpot",
    "Outcome",
    "SourceName",
    "SourceUrl",
    "LoadedAt",
    "RecordKey",
]


SUMMARY_COLUMNS = [
    "Metric",
    "Value",
]


UPDATE_LOG_COLUMNS = [
    "RunTimestamp",
    "UpdateType",
    "GameFamily",
    "GameName",
    "DrawType",
    "RowsFetched",
    "RowsAdded",
    "RowsSkipped",
    "Status",
    "Notes",
]


# =========================================================
# VALID GAME NAMES
# =========================================================

VALID_GAME_CONFIG = {
    "PowerBall": {
        "family": "PowerBall",
        "games": ["PowerBall", "PowerBall Plus"],
    },
    "Lotto": {
        "family": "Lotto",
        "games": ["Lotto", "Lotto Plus 1", "Lotto Plus 2"],
    },
    "Daily Lotto": {
        "family": "Daily Lotto",
        "games": ["Daily Lotto"],
    },
    "UK49s": {
        "family": "UK49s",
        "games": ["UK49s Lunchtime", "UK49s Teatime"],
    },
}


# =========================================================
# EMPTY DATAFRAMES
# =========================================================

def empty_historical_df():
    return pd.DataFrame(columns=HISTORICAL_COLUMNS)


def empty_summary_df():
    return pd.DataFrame(columns=SUMMARY_COLUMNS)


def empty_update_log_df():
    return pd.DataFrame(columns=UPDATE_LOG_COLUMNS)


# =========================================================
# DATA CLEANING HELPERS
# =========================================================

def normalise_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def normalise_draw_date(value):
    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.strftime("%Y-%m-%d")


def get_draw_day(value):
    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return ""

    return parsed.day_name()


def normalise_number(value):
    if pd.isna(value) or value == "":
        return None

    try:
        return int(value)
    except Exception:
        return None


def normalise_jackpot(value):
    if pd.isna(value) or value == "":
        return None

    text = str(value)
    text = text.replace("R", "")
    text = text.replace(",", "")
    text = text.strip()

    try:
        return float(text)
    except Exception:
        return None


# =========================================================
# RECORD KEY
# =========================================================

def build_record_key(row):
    parts = [
        normalise_text(row.get("GameFamily")),
        normalise_text(row.get("GameName")),
        normalise_text(row.get("DrawType")),
        normalise_text(row.get("DrawDate")),
        normalise_text(row.get("N1")),
        normalise_text(row.get("N2")),
        normalise_text(row.get("N3")),
        normalise_text(row.get("N4")),
        normalise_text(row.get("N5")),
        normalise_text(row.get("N6")),
        normalise_text(row.get("Bonus")),
    ]

    return "|".join(parts)


# =========================================================
# ROW BUILDER
# =========================================================

def build_history_row(
    game_family,
    game_name,
    draw_type,
    draw_date,
    n1=None,
    n2=None,
    n3=None,
    n4=None,
    n5=None,
    n6=None,
    bonus=None,
    draw_number=None,
    jackpot=None,
    outcome=None,
    source_name=None,
    source_url=None,
):
    clean_draw_date = normalise_draw_date(draw_date)

    row = {
        "GameFamily": normalise_text(game_family),
        "GameName": normalise_text(game_name),
        "DrawType": normalise_text(draw_type),
        "DrawNumber": normalise_text(draw_number),
        "DrawDate": clean_draw_date,
        "DrawDay": get_draw_day(clean_draw_date),
        "N1": normalise_number(n1),
        "N2": normalise_number(n2),
        "N3": normalise_number(n3),
        "N4": normalise_number(n4),
        "N5": normalise_number(n5),
        "N6": normalise_number(n6),
        "Bonus": normalise_number(bonus),
        "Jackpot": normalise_jackpot(jackpot),
        "Outcome": normalise_text(outcome),
        "SourceName": normalise_text(source_name),
        "SourceUrl": normalise_text(source_url),
        "LoadedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    row["RecordKey"] = build_record_key(row)

    return row


# =========================================================
# DATAFRAME STANDARDISER
# =========================================================

def standardise_historical_df(df):
    if df is None or df.empty:
        return empty_historical_df()

    for col in HISTORICAL_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df = df[HISTORICAL_COLUMNS].copy()

    df["DrawDate"] = df["DrawDate"].apply(normalise_draw_date)
    df["DrawDay"] = df["DrawDate"].apply(get_draw_day)

    number_cols = ["N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]

    for col in number_cols:
        df[col] = df[col].apply(normalise_number)

    df["Jackpot"] = df["Jackpot"].apply(normalise_jackpot)

    text_cols = [
        "GameFamily",
        "GameName",
        "DrawType",
        "DrawNumber",
        "Outcome",
        "SourceName",
        "SourceUrl",
        "LoadedAt",
    ]

    for col in text_cols:
        df[col] = df[col].apply(normalise_text)

    df["RecordKey"] = df.apply(build_record_key, axis=1)

    df = df.dropna(subset=["DrawDate", "N1", "N2", "N3", "N4", "N5"])

    df = df.drop_duplicates(subset=["RecordKey"], keep="first")

    df["DrawDateSort"] = pd.to_datetime(df["DrawDate"], errors="coerce")

    df = df.sort_values(
        by=["DrawDateSort", "GameFamily", "GameName", "DrawType"],
        ascending=[False, True, True, True]
    )

    df = df.drop(columns=["DrawDateSort"])

    df = df.reset_index(drop=True)

    return df


# =========================================================
# SUMMARY BUILDER
# =========================================================

def build_summary(df):
    df = standardise_historical_df(df)

    if df.empty:
        return pd.DataFrame([
            {"Metric": "Total Rows", "Value": 0},
            {"Metric": "Latest Draw Date", "Value": ""},
            {"Metric": "Earliest Draw Date", "Value": ""},
            {"Metric": "Game Families", "Value": 0},
            {"Metric": "Game Names", "Value": 0},
            {"Metric": "Last Updated", "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        ])

    date_series = pd.to_datetime(df["DrawDate"], errors="coerce")

    return pd.DataFrame([
        {"Metric": "Total Rows", "Value": len(df)},
        {"Metric": "Latest Draw Date", "Value": date_series.max().strftime("%Y-%m-%d")},
        {"Metric": "Earliest Draw Date", "Value": date_series.min().strftime("%Y-%m-%d")},
        {"Metric": "Game Families", "Value": df["GameFamily"].nunique()},
        {"Metric": "Game Names", "Value": df["GameName"].nunique()},
        {"Metric": "PowerBall Rows", "Value": int((df["GameFamily"] == "PowerBall").sum())},
        {"Metric": "Lotto Rows", "Value": int((df["GameFamily"] == "Lotto").sum())},
        {"Metric": "Daily Lotto Rows", "Value": int((df["GameFamily"] == "Daily Lotto").sum())},
        {"Metric": "UK49s Rows", "Value": int((df["GameFamily"] == "UK49s").sum())},
        {"Metric": "Last Updated", "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    ])


# =========================================================
# UPDATE LOG BUILDER
# =========================================================

def build_update_log_row(
    update_type,
    game_family,
    game_name,
    draw_type,
    rows_fetched,
    rows_added,
    rows_skipped,
    status,
    notes="",
):
    return {
        "RunTimestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "UpdateType": normalise_text(update_type),
        "GameFamily": normalise_text(game_family),
        "GameName": normalise_text(game_name),
        "DrawType": normalise_text(draw_type),
        "RowsFetched": int(rows_fetched),
        "RowsAdded": int(rows_added),
        "RowsSkipped": int(rows_skipped),
        "Status": normalise_text(status),
        "Notes": normalise_text(notes),
    }


# =========================================================
# VALIDATION
# =========================================================

def validate_history_df(df):
    issues = []

    df = standardise_historical_df(df)

    if df.empty:
        issues.append("Historical dataframe is empty.")
        return issues

    required = ["GameFamily", "GameName", "DrawDate", "N1", "N2", "N3", "N4", "N5"]

    for col in required:
        missing_count = df[col].isna().sum()

        if missing_count > 0:
            issues.append(f"{col} has {missing_count} missing values.")

    number_cols = ["N1", "N2", "N3", "N4", "N5"]

    for col in number_cols:
        invalid_count = df[
            (df[col] < 1) | (df[col] > 59)
        ].shape[0]

        if invalid_count > 0:
            issues.append(f"{col} has {invalid_count} values outside expected lottery range.")

    duplicate_count = df.duplicated(subset=["RecordKey"]).sum()

    if duplicate_count > 0:
        issues.append(f"{duplicate_count} duplicate RecordKey values found.")

    return issues


# =========================================================
# QUICK TEST
# =========================================================

if __name__ == "__main__":
    sample = build_history_row(
        game_family="PowerBall",
        game_name="PowerBall Plus",
        draw_type="Plus",
        draw_date="2026-05-10",
        n1=5,
        n2=11,
        n3=23,
        n4=29,
        n5=48,
        bonus=1,
        jackpot="R25,000,000",
        outcome="Roll",
        source_name="za.national-lottery.com",
        source_url="https://za.national-lottery.com/powerball-plus/results/history",
    )

    df = pd.DataFrame([sample])

    print(standardise_historical_df(df))
    print(build_summary(df))
    print(validate_history_df(df))