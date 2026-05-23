from pathlib import Path
from datetime import datetime

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

MASTER_FILE = BASE_DIR / "data" / "master" / "lottery_historical_master.xlsx"
QUALITY_DIR = BASE_DIR / "data" / "processed" / "quality"
QUALITY_FILE = QUALITY_DIR / "lottery_quality_report.xlsx"

HISTORICAL_SHEET = "Historical_Results"


# =========================================================
# EXPECTED GAME CONFIG
# =========================================================

GAME_RULES = {
    "PowerBall": {
        "regular_min": 1,
        "regular_max": 50,
        "bonus_min": 1,
        "bonus_max": 20,
        "regular_count": 5,
    },
    "Lotto": {
        "regular_min": 1,
        "regular_max": 58,
        "bonus_min": 1,
        "bonus_max": 58,
        "regular_count": 6,
    },
    "Daily Lotto": {
        "regular_min": 1,
        "regular_max": 36,
        "bonus_min": None,
        "bonus_max": None,
        "regular_count": 5,
    },
    "UK49s": {
        "regular_min": 1,
        "regular_max": 49,
        "bonus_min": 1,
        "bonus_max": 49,
        "regular_count": 6,
    },
}


# =========================================================
# LOAD DATA
# =========================================================

def load_history():
    if not MASTER_FILE.exists():
        raise FileNotFoundError(
            f"Master file not found: {MASTER_FILE}"
        )

    df = pd.read_excel(
        MASTER_FILE,
        sheet_name=HISTORICAL_SHEET,
        engine="openpyxl"
    )

    return df


def clean_history(df):
    df = df.copy()

    df["DrawDate"] = pd.to_datetime(
        df["DrawDate"],
        errors="coerce"
    )

    number_cols = [
        "N1",
        "N2",
        "N3",
        "N4",
        "N5",
        "N6",
        "Bonus",
    ]

    for col in number_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return df


# =========================================================
# QUALITY CHECKS
# =========================================================

def check_summary(df):
    total_rows = len(df)

    summary_rows = [
        {
            "Metric": "Total Rows",
            "Value": total_rows,
        },
        {
            "Metric": "Unique Game Families",
            "Value": df["GameFamily"].nunique(),
        },
        {
            "Metric": "Unique Game Names",
            "Value": df["GameName"].nunique(),
        },
        {
            "Metric": "Earliest Draw Date",
            "Value": df["DrawDate"].min(),
        },
        {
            "Metric": "Latest Draw Date",
            "Value": df["DrawDate"].max(),
        },
        {
            "Metric": "Duplicate RecordKeys",
            "Value": df.duplicated(subset=["RecordKey"]).sum()
            if "RecordKey" in df.columns else "RecordKey column missing",
        },
        {
            "Metric": "Report Generated At",
            "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    ]

    return pd.DataFrame(summary_rows)


def check_row_counts(df):
    rows = []

    grouped = df.groupby(
        ["GameFamily", "GameName", "DrawType"],
        dropna=False
    )

    for keys, group in grouped:
        game_family, game_name, draw_type = keys

        rows.append({
            "GameFamily": game_family,
            "GameName": game_name,
            "DrawType": draw_type,
            "Rows": len(group),
            "EarliestDrawDate": group["DrawDate"].min(),
            "LatestDrawDate": group["DrawDate"].max(),
            "UniqueDrawDates": group["DrawDate"].nunique(),
        })

    return pd.DataFrame(rows)


def check_missing_values(df):
    important_cols = [
        "GameFamily",
        "GameName",
        "DrawType",
        "DrawDate",
        "N1",
        "N2",
        "N3",
        "N4",
        "N5",
        "RecordKey",
    ]

    rows = []

    for col in important_cols:
        if col not in df.columns:
            rows.append({
                "Column": col,
                "MissingCount": "Column Missing",
                "MissingPercent": "Column Missing",
            })
            continue

        missing_count = df[col].isna().sum()
        missing_percent = round(
            (missing_count / len(df)) * 100,
            2
        ) if len(df) else 0

        rows.append({
            "Column": col,
            "MissingCount": missing_count,
            "MissingPercent": missing_percent,
        })

    return pd.DataFrame(rows)


def check_duplicates(df):
    if "RecordKey" not in df.columns:
        return pd.DataFrame([
            {
                "Issue": "RecordKey column missing",
                "RecordKey": "",
                "DuplicateCount": "",
            }
        ])

    duplicate_rows = df[
        df.duplicated(subset=["RecordKey"], keep=False)
    ].copy()

    if duplicate_rows.empty:
        return pd.DataFrame(columns=[
            "RecordKey",
            "DuplicateCount",
            "GameFamily",
            "GameName",
            "DrawType",
            "DrawDate",
        ])

    counts = duplicate_rows["RecordKey"].value_counts()

    duplicate_rows["DuplicateCount"] = duplicate_rows["RecordKey"].map(counts)

    return duplicate_rows[
        [
            "RecordKey",
            "DuplicateCount",
            "GameFamily",
            "GameName",
            "DrawType",
            "DrawDate",
        ]
    ].sort_values(
        by=["DuplicateCount", "RecordKey"],
        ascending=[False, True]
    )


def check_number_ranges(df):
    issue_rows = []

    regular_cols = ["N1", "N2", "N3", "N4", "N5", "N6"]

    for idx, row in df.iterrows():
        game_family = row.get("GameFamily")

        rules = GAME_RULES.get(game_family)

        if rules is None:
            issue_rows.append({
                "RowIndex": idx,
                "GameFamily": game_family,
                "GameName": row.get("GameName"),
                "DrawDate": row.get("DrawDate"),
                "Issue": "Unknown GameFamily",
                "Column": "",
                "Value": "",
                "Expected": "",
            })
            continue

        regular_min = rules["regular_min"]
        regular_max = rules["regular_max"]
        bonus_min = rules["bonus_min"]
        bonus_max = rules["bonus_max"]
        regular_count = rules["regular_count"]

        used_regular_cols = regular_cols[:regular_count]

        for col in used_regular_cols:
            value = row.get(col)

            if pd.isna(value):
                issue_rows.append({
                    "RowIndex": idx,
                    "GameFamily": game_family,
                    "GameName": row.get("GameName"),
                    "DrawDate": row.get("DrawDate"),
                    "Issue": "Missing regular number",
                    "Column": col,
                    "Value": value,
                    "Expected": f"{regular_min}-{regular_max}",
                })
                continue

            if value < regular_min or value > regular_max:
                issue_rows.append({
                    "RowIndex": idx,
                    "GameFamily": game_family,
                    "GameName": row.get("GameName"),
                    "DrawDate": row.get("DrawDate"),
                    "Issue": "Regular number outside expected range",
                    "Column": col,
                    "Value": value,
                    "Expected": f"{regular_min}-{regular_max}",
                })

        unused_regular_cols = regular_cols[regular_count:]

        for col in unused_regular_cols:
            value = row.get(col)

            if pd.notna(value):
                issue_rows.append({
                    "RowIndex": idx,
                    "GameFamily": game_family,
                    "GameName": row.get("GameName"),
                    "DrawDate": row.get("DrawDate"),
                    "Issue": "Unexpected extra regular number",
                    "Column": col,
                    "Value": value,
                    "Expected": "Blank",
                })

        bonus = row.get("Bonus")

        if bonus_min is None and pd.notna(bonus):
            issue_rows.append({
                "RowIndex": idx,
                "GameFamily": game_family,
                "GameName": row.get("GameName"),
                "DrawDate": row.get("DrawDate"),
                "Issue": "Unexpected bonus number",
                "Column": "Bonus",
                "Value": bonus,
                "Expected": "Blank",
            })

        if bonus_min is not None:
            if pd.isna(bonus):
                issue_rows.append({
                    "RowIndex": idx,
                    "GameFamily": game_family,
                    "GameName": row.get("GameName"),
                    "DrawDate": row.get("DrawDate"),
                    "Issue": "Missing bonus number",
                    "Column": "Bonus",
                    "Value": bonus,
                    "Expected": f"{bonus_min}-{bonus_max}",
                })

            elif bonus < bonus_min or bonus > bonus_max:
                issue_rows.append({
                    "RowIndex": idx,
                    "GameFamily": game_family,
                    "GameName": row.get("GameName"),
                    "DrawDate": row.get("DrawDate"),
                    "Issue": "Bonus number outside expected range",
                    "Column": "Bonus",
                    "Value": bonus,
                    "Expected": f"{bonus_min}-{bonus_max}",
                })

    return pd.DataFrame(issue_rows)


def check_duplicate_numbers_within_draw(df):
    issue_rows = []

    regular_cols = ["N1", "N2", "N3", "N4", "N5", "N6"]

    for idx, row in df.iterrows():
        game_family = row.get("GameFamily")
        rules = GAME_RULES.get(game_family)

        if rules is None:
            continue

        regular_count = rules["regular_count"]
        used_cols = regular_cols[:regular_count]

        numbers = []

        for col in used_cols:
            value = row.get(col)

            if pd.notna(value):
                numbers.append(int(value))

        if len(numbers) != len(set(numbers)):
            issue_rows.append({
                "RowIndex": idx,
                "GameFamily": game_family,
                "GameName": row.get("GameName"),
                "DrawType": row.get("DrawType"),
                "DrawDate": row.get("DrawDate"),
                "Numbers": ", ".join(map(str, numbers)),
                "Issue": "Duplicate regular number within same draw",
            })

    return pd.DataFrame(issue_rows)


def check_latest_dates(df):
    rows = []

    grouped = df.groupby(
        ["GameFamily", "GameName", "DrawType"],
        dropna=False
    )

    for keys, group in grouped:
        game_family, game_name, draw_type = keys

        latest_date = group["DrawDate"].max()
        earliest_date = group["DrawDate"].min()

        rows.append({
            "GameFamily": game_family,
            "GameName": game_name,
            "DrawType": draw_type,
            "LatestDrawDate": latest_date,
            "EarliestDrawDate": earliest_date,
            "Rows": len(group),
        })

    return pd.DataFrame(rows)


# =========================================================
# QUALITY REPORT
# =========================================================

def run_quality_checks():
    QUALITY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df = load_history()
    df = clean_history(df)

    summary = check_summary(df)
    row_counts = check_row_counts(df)
    missing_values = check_missing_values(df)
    duplicates = check_duplicates(df)
    number_range_issues = check_number_ranges(df)
    duplicate_number_issues = check_duplicate_numbers_within_draw(df)
    latest_dates = check_latest_dates(df)

    with pd.ExcelWriter(
        QUALITY_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:
        summary.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        row_counts.to_excel(
            writer,
            sheet_name="Row_Counts",
            index=False
        )

        missing_values.to_excel(
            writer,
            sheet_name="Missing_Values",
            index=False
        )

        duplicates.to_excel(
            writer,
            sheet_name="Duplicate_RecordKeys",
            index=False
        )

        number_range_issues.to_excel(
            writer,
            sheet_name="Number_Range_Issues",
            index=False
        )

        duplicate_number_issues.to_excel(
            writer,
            sheet_name="Duplicate_Number_Issues",
            index=False
        )

        latest_dates.to_excel(
            writer,
            sheet_name="Latest_Dates",
            index=False
        )

    print("\nLottery quality checks complete.")
    print(f"Rows checked: {len(df)}")
    print(f"Duplicate RecordKeys: {len(duplicates)}")
    print(f"Number range issues: {len(number_range_issues)}")
    print(f"Duplicate number issues: {len(duplicate_number_issues)}")
    print(f"File: {QUALITY_FILE}")

    return {
        "rows_checked": len(df),
        "duplicate_recordkeys": len(duplicates),
        "number_range_issues": len(number_range_issues),
        "duplicate_number_issues": len(duplicate_number_issues),
        "file": QUALITY_FILE,
    }


# =========================================================
# QUICK TEST
# =========================================================

if __name__ == "__main__":
    run_quality_checks()