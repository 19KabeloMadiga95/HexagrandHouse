from pathlib import Path

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

MASTER_FILE = BASE_DIR / "data" / "master" / "lottery_historical_master.xlsx"
FEATURES_DIR = BASE_DIR / "data" / "processed" / "features"

HISTORICAL_SHEET = "Historical_Results"


# =========================================================
# LOAD MASTER HISTORY
# =========================================================

def load_lottery_history():
    if not MASTER_FILE.exists():
        raise FileNotFoundError(
            f"Master history file not found: {MASTER_FILE}"
        )

    df = pd.read_excel(
        MASTER_FILE,
        sheet_name=HISTORICAL_SHEET,
        engine="openpyxl"
    )

    return df


# =========================================================
# BASIC CLEANING
# =========================================================

def clean_history(df):
    df = df.copy()

    df["DrawDate"] = pd.to_datetime(df["DrawDate"], errors="coerce")

    number_cols = ["N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]

    for col in number_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["DrawDate", "N1", "N2", "N3", "N4", "N5"])

    df = df.sort_values(
        by=["GameFamily", "GameName", "DrawType", "DrawDate"],
        ascending=[True, True, True, False]
    ).reset_index(drop=True)

    return df


# =========================================================
# ROW FEATURE HELPERS
# =========================================================

def get_regular_numbers(row):
    numbers = []

    for col in ["N1", "N2", "N3", "N4", "N5", "N6"]:
        value = row.get(col)

        if pd.notna(value):
            numbers.append(int(value))

    return numbers


def count_consecutive_pairs(numbers):
    numbers = sorted(numbers)

    count = 0

    for i in range(len(numbers) - 1):
        if numbers[i + 1] - numbers[i] == 1:
            count += 1

    return count


def count_low_numbers(numbers, low_threshold):
    return sum(1 for n in numbers if n <= low_threshold)


def count_high_numbers(numbers, low_threshold):
    return sum(1 for n in numbers if n > low_threshold)


def odd_count(numbers):
    return sum(1 for n in numbers if n % 2 != 0)


def even_count(numbers):
    return sum(1 for n in numbers if n % 2 == 0)


# =========================================================
# FEATURE BUILDER
# =========================================================

def add_base_features(df):
    df = clean_history(df)

    feature_rows = []

    for _, row in df.iterrows():
        numbers = get_regular_numbers(row)

        if not numbers:
            continue

        game_family = row.get("GameFamily", "")
        game_name = row.get("GameName", "")
        draw_type = row.get("DrawType", "")

        number_count = len(numbers)

        max_regular = max(numbers)
        min_regular = min(numbers)

        if max_regular <= 36:
            low_threshold = 18
        elif max_regular <= 49:
            low_threshold = 24
        elif max_regular <= 50:
            low_threshold = 25
        else:
            low_threshold = 30

        regular_sum = sum(numbers)
        odds = odd_count(numbers)
        evens = even_count(numbers)
        lows = count_low_numbers(numbers, low_threshold)
        highs = count_high_numbers(numbers, low_threshold)

        sorted_numbers = sorted(numbers)
        gaps = []

        for i in range(len(sorted_numbers) - 1):
            gaps.append(sorted_numbers[i + 1] - sorted_numbers[i])

        if gaps:
            average_gap = round(sum(gaps) / len(gaps), 2)
            min_gap = min(gaps)
            max_gap = max(gaps)
        else:
            average_gap = 0
            min_gap = 0
            max_gap = 0

        bonus = row.get("Bonus")
        has_bonus = 1 if pd.notna(bonus) else 0

        feature_rows.append({
            "GameFamily": game_family,
            "GameName": game_name,
            "DrawType": draw_type,
            "DrawDate": row.get("DrawDate"),
            "DrawDay": row.get("DrawDay"),
            "DrawNumber": row.get("DrawNumber"),
            "N1": row.get("N1"),
            "N2": row.get("N2"),
            "N3": row.get("N3"),
            "N4": row.get("N4"),
            "N5": row.get("N5"),
            "N6": row.get("N6"),
            "Bonus": row.get("Bonus"),
            "NumberCount": number_count,
            "RegularSum": regular_sum,
            "AverageNumber": round(regular_sum / number_count, 2),
            "MinNumber": min_regular,
            "MaxNumber": max_regular,
            "NumberSpread": max_regular - min_regular,
            "OddCount": odds,
            "EvenCount": evens,
            "LowCount": lows,
            "HighCount": highs,
            "LowThresholdUsed": low_threshold,
            "ConsecutivePairs": count_consecutive_pairs(numbers),
            "AverageGap": average_gap,
            "MinGap": min_gap,
            "MaxGap": max_gap,
            "HasBonus": has_bonus,
            "SourceName": row.get("SourceName", ""),
            "SourceUrl": row.get("SourceUrl", ""),
            "RecordKey": row.get("RecordKey", ""),
        })

    features = pd.DataFrame(feature_rows)

    features = features.sort_values(
        by=["GameFamily", "GameName", "DrawType", "DrawDate"],
        ascending=[True, True, True, False]
    ).reset_index(drop=True)

    return features


# =========================================================
# EXPORT
# =========================================================

def export_base_features():
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)

    df = load_lottery_history()
    features = add_base_features(df)

    output_file = FEATURES_DIR / "base_lottery_features.xlsx"

    features.to_excel(
        output_file,
        sheet_name="Base_Features",
        index=False
    )

    print("\nBase lottery features exported.")
    print(f"Rows: {len(features)}")
    print(f"File: {output_file}")

    return features


# =========================================================
# QUICK TEST
# =========================================================

if __name__ == "__main__":
    export_base_features()