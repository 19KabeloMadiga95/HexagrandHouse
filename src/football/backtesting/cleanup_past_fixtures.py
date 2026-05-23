from pathlib import Path
from datetime import datetime

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

PREDICTIONS_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "predictions"
)

REPORTING_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "reporting"
)

VALUE_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "value"
)

FIXTURE_PREDICTIONS_FILE = (
    PREDICTIONS_DIR
    / "football_fixture_predictions.xlsx"
)

TOP_PLAYS_FILE = (
    REPORTING_DIR
    / "top_plays_report.xlsx"
)

VALUE_BETS_FILE = (
    VALUE_DIR
    / "football_value_bets.xlsx"
)


# =========================================================
# HELPERS
# =========================================================

def safe_read_excel(path, sheet_name=0):
    try:
        if not path.exists():
            return pd.DataFrame()

        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )

    except Exception:
        return pd.DataFrame()


def build_fixture_datetime(df):
    if df.empty:
        return df

    df = df.copy()

    if "FixtureDate" not in df.columns:
        df["FixtureDateTime"] = pd.NaT
        return df

    if "KickoffTime" not in df.columns:
        df["KickoffTime"] = "12:00"

    df["FixtureDateTime"] = pd.to_datetime(
        df["FixtureDate"].astype(str)
        + " "
        + df["KickoffTime"].fillna("12:00").astype(str),
        errors="coerce"
    )

    return df


def keep_upcoming_only(df):
    if df.empty:
        return df

    df = build_fixture_datetime(df)

    now = pd.Timestamp.now()

    return df[
        df["FixtureDateTime"].notna()
        & (df["FixtureDateTime"] >= now)
    ].copy()


def export_single_sheet(path, sheet_name, df):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with pd.ExcelWriter(
        path,
        engine="openpyxl",
        mode="w"
    ) as writer:
        df.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False
        )


def cleanup_fixture_predictions():
    df = safe_read_excel(
        FIXTURE_PREDICTIONS_FILE,
        "Fixture_Predictions"
    )

    if df.empty:
        df = safe_read_excel(
            FIXTURE_PREDICTIONS_FILE
        )

    before_count = len(df)

    cleaned_df = keep_upcoming_only(df)

    after_count = len(cleaned_df)

    export_single_sheet(
        FIXTURE_PREDICTIONS_FILE,
        "Fixture_Predictions",
        cleaned_df
    )

    return {
        "File": str(FIXTURE_PREDICTIONS_FILE),
        "BeforeRows": before_count,
        "AfterRows": after_count,
        "RemovedRows": before_count - after_count,
    }


def cleanup_top_plays():
    df = safe_read_excel(
        TOP_PLAYS_FILE,
        "Top_Plays"
    )

    if df.empty:
        df = safe_read_excel(
            TOP_PLAYS_FILE
        )

    before_count = len(df)

    cleaned_df = keep_upcoming_only(df)

    after_count = len(cleaned_df)

    export_single_sheet(
        TOP_PLAYS_FILE,
        "Top_Plays",
        cleaned_df
    )

    return {
        "File": str(TOP_PLAYS_FILE),
        "BeforeRows": before_count,
        "AfterRows": after_count,
        "RemovedRows": before_count - after_count,
    }


def cleanup_value_bets():
    df = safe_read_excel(
        VALUE_BETS_FILE,
        "Value_Bets"
    )

    if df.empty:
        df = safe_read_excel(
            VALUE_BETS_FILE
        )

    before_count = len(df)

    cleaned_df = keep_upcoming_only(df)

    after_count = len(cleaned_df)

    export_single_sheet(
        VALUE_BETS_FILE,
        "Value_Bets",
        cleaned_df
    )

    return {
        "File": str(VALUE_BETS_FILE),
        "BeforeRows": before_count,
        "AfterRows": after_count,
        "RemovedRows": before_count - after_count,
    }


def cleanup_past_fixtures():
    results = []

    results.append(
        cleanup_fixture_predictions()
    )

    results.append(
        cleanup_top_plays()
    )

    results.append(
        cleanup_value_bets()
    )

    summary_df = pd.DataFrame(results)

    print("\n======================================")
    print("PAST FOOTBALL FIXTURES CLEANED")
    print("======================================")

    for row in results:
        print(f"File        : {row['File']}")
        print(f"Before rows : {row['BeforeRows']}")
        print(f"After rows  : {row['AfterRows']}")
        print(f"Removed     : {row['RemovedRows']}")
        print("--------------------------------------")

    print(f"Cleaned At  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("======================================\n")

    return summary_df


def main():
    cleanup_past_fixtures()


if __name__ == "__main__":
    main()