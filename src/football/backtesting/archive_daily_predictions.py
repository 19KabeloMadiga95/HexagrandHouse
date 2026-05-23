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

BACKTEST_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "backtesting"
)

SNAPSHOT_DIR = (
    BACKTEST_DIR
    / "prediction_snapshots"
)

PREDICTIONS_FILE = (
    PREDICTIONS_DIR
    / "football_fixture_predictions.xlsx"
)

ARCHIVE_CSV = (
    BACKTEST_DIR
    / "prediction_snapshot_archive.csv"
)

ARCHIVE_EXCEL = (
    BACKTEST_DIR
    / "prediction_snapshot_archive.xlsx"
)


# =========================================================
# HELPERS
# =========================================================

def ensure_directories():
    BACKTEST_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    SNAPSHOT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def safe_read_excel(path, sheet_name=0):
    try:
        if not path.exists():
            print(f"Missing file: {path}")
            return pd.DataFrame()

        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )

    except Exception as e:
        print(f"Could not read file: {path}")
        print(f"Error: {e}")
        return pd.DataFrame()


def safe_read_archive():
    if not ARCHIVE_CSV.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(
            ARCHIVE_CSV,
            low_memory=False
        )

    except Exception as e:
        print(f"Could not read archive: {ARCHIVE_CSV}")
        print(f"Error: {e}")
        return pd.DataFrame()


def clean_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def build_archive_key(df):
    df = df.copy()

    required_cols = [
        "LeagueCode",
        "FixtureDate",
        "HomeTeam",
        "AwayTeam",
        "PredictedResult",
    ]

    for col in required_cols:
        if col not in df.columns:
            df[col] = ""

    fixture_date = pd.to_datetime(
        df["FixtureDate"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df["ArchiveKey"] = (
        df["LeagueCode"].apply(clean_text).str.upper()
        + "_"
        + fixture_date.fillna("")
        + "_"
        + df["HomeTeam"].apply(clean_text).str.lower()
        + "_"
        + df["AwayTeam"].apply(clean_text).str.lower()
        + "_"
        + df["PredictedResult"].apply(clean_text).str.lower()
    )

    return df


def add_snapshot_metadata(df):
    df = df.copy()

    snapshot_time = datetime.now()

    df["SnapshotDate"] = snapshot_time.strftime(
        "%Y-%m-%d"
    )

    df["SnapshotTimestamp"] = snapshot_time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    df["SnapshotSource"] = "football_fixture_predictions"

    return df


def build_snapshot_filename():
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return (
        SNAPSHOT_DIR
        / f"football_fixture_predictions_snapshot_{timestamp}.xlsx"
    )


def export_snapshot_file(snapshot_df):
    snapshot_file = build_snapshot_filename()

    with pd.ExcelWriter(
        snapshot_file,
        engine="openpyxl",
        mode="w"
    ) as writer:
        snapshot_df.to_excel(
            writer,
            sheet_name="Fixture_Predictions",
            index=False
        )

    return snapshot_file


def export_archive_files(archive_df):
    archive_df.to_csv(
        ARCHIVE_CSV,
        index=False
    )

    with pd.ExcelWriter(
        ARCHIVE_EXCEL,
        engine="openpyxl",
        mode="w"
    ) as writer:
        archive_df.to_excel(
            writer,
            sheet_name="Prediction_Archive",
            index=False
        )


def archive_daily_predictions():
    ensure_directories()

    predictions_df = safe_read_excel(
        PREDICTIONS_FILE,
        "Fixture_Predictions"
    )

    if predictions_df.empty:
        predictions_df = safe_read_excel(
            PREDICTIONS_FILE
        )

    if predictions_df.empty:
        print("No fixture predictions available to archive.")
        return pd.DataFrame()

    snapshot_df = predictions_df.copy()

    snapshot_df = add_snapshot_metadata(
        snapshot_df
    )

    snapshot_df = build_archive_key(
        snapshot_df
    )

    existing_archive_df = safe_read_archive()

    if existing_archive_df.empty:
        archive_df = snapshot_df.copy()
    else:
        archive_df = pd.concat(
            [
                existing_archive_df,
                snapshot_df,
            ],
            ignore_index=True
        )

    archive_df = build_archive_key(
        archive_df
    )

    archive_df = archive_df.drop_duplicates(
        subset=[
            "ArchiveKey",
            "SnapshotDate",
        ],
        keep="last"
    ).reset_index(drop=True)

    snapshot_file = export_snapshot_file(
        snapshot_df
    )

    export_archive_files(
        archive_df
    )

    print("\n======================================")
    print("FOOTBALL DAILY PREDICTIONS ARCHIVED")
    print("======================================")
    print(f"Snapshot rows : {len(snapshot_df)}")
    print(f"Archive rows  : {len(archive_df)}")
    print(f"Snapshot file : {snapshot_file}")
    print(f"Archive CSV   : {ARCHIVE_CSV}")
    print(f"Archive Excel : {ARCHIVE_EXCEL}")
    print("======================================\n")

    return archive_df


def main():
    archive_daily_predictions()


if __name__ == "__main__":
    main()