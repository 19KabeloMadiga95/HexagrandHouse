from __future__ import annotations

import pandas as pd

from src.data.database import read_lottery_history
from src.data.sqlite_store import replace_sqlite_table, create_indexes
from src.lottery.config.lottery_game_rules import get_rule_for_draw


# =========================================================
# SQLITE TABLES
# =========================================================

BASE_FEATURES_TABLE = "lottery_base_features"


# =========================================================
# LOAD HISTORY FROM SQLITE
# =========================================================


def load_lottery_history() -> pd.DataFrame:
    """
    Load lottery history from SQLite.

    Excel is no longer the runtime source for feature generation.
    The authoritative runtime source is data/hexagrandhouse.db.
    """

    df = read_lottery_history()

    if df.empty:
        raise RuntimeError(
            "SQLite table 'lottery_history' is empty or missing. "
            "Build/populate data/hexagrandhouse.db before running features."
        )

    return df


# =========================================================
# BASIC CLEANING
# =========================================================


def clean_history(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "DrawDate" in df.columns:
        df["DrawDate"] = pd.to_datetime(df["DrawDate"], errors="coerce")
    else:
        df["DrawDate"] = pd.NaT

    number_cols = ["N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]

    for col in number_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = pd.NA

    required_cols = ["DrawDate", "N1", "N2", "N3", "N4", "N5"]
    df = df.dropna(subset=[col for col in required_cols if col in df.columns])

    for col in ["GameFamily", "GameName", "DrawType", "DrawDay", "DrawNumber"]:
        if col not in df.columns:
            df[col] = ""

    df = df.sort_values(
        by=["GameFamily", "GameName", "DrawType", "DrawDate"],
        ascending=[True, True, True, False],
    ).reset_index(drop=True)

    return df


# =========================================================
# ROW FEATURE HELPERS
# =========================================================


def get_regular_numbers(row: pd.Series) -> list[int]:
    numbers: list[int] = []

    for col in ["N1", "N2", "N3", "N4", "N5", "N6"]:
        value = row.get(col)

        if pd.notna(value):
            numbers.append(int(value))

    return numbers


def count_consecutive_pairs(numbers: list[int]) -> int:
    numbers = sorted(numbers)
    return sum(1 for i in range(len(numbers) - 1) if numbers[i + 1] - numbers[i] == 1)


def odd_count(numbers: list[int]) -> int:
    return sum(1 for n in numbers if n % 2 != 0)


def even_count(numbers: list[int]) -> int:
    return sum(1 for n in numbers if n % 2 == 0)


def _fallback_low_threshold(numbers: list[int]) -> int:
    max_regular = max(numbers)

    if max_regular <= 36:
        return 18
    if max_regular <= 49:
        return 24
    if max_regular <= 50:
        return 25
    if max_regular <= 52:
        return 26
    return 29


def _rule_threshold(game_name: str, draw_date, numbers: list[int]) -> tuple[int, str, str]:
    rule = get_rule_for_draw(game_name, draw_date)

    if rule is None:
        threshold = _fallback_low_threshold(numbers)
        return threshold, "Unknown", "Unknown"

    threshold = rule.regular_max // 2
    regular_range = f"{rule.regular_min}-{rule.regular_max}"
    bonus_range = (
        f"{rule.bonus_min}-{rule.bonus_max}"
        if rule.bonus_min is not None and rule.bonus_max is not None
        else "None"
    )

    return threshold, regular_range, bonus_range


# =========================================================
# FEATURE BUILDER
# =========================================================


def add_base_features(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_history(df)
    feature_rows: list[dict] = []

    for _, row in df.iterrows():
        numbers = get_regular_numbers(row)

        if not numbers:
            continue

        game_family = row.get("GameFamily", "")
        game_name = row.get("GameName", "")
        draw_type = row.get("DrawType", "")
        draw_date = row.get("DrawDate")

        number_count = len(numbers)
        max_regular = max(numbers)
        min_regular = min(numbers)
        low_threshold, regular_range, bonus_range = _rule_threshold(game_name, draw_date, numbers)

        lows = sum(1 for n in numbers if n <= low_threshold)
        highs = sum(1 for n in numbers if n > low_threshold)
        regular_sum = sum(numbers)
        sorted_numbers = sorted(numbers)
        gaps = [sorted_numbers[i + 1] - sorted_numbers[i] for i in range(len(sorted_numbers) - 1)]

        bonus = row.get("Bonus")
        has_bonus = 1 if pd.notna(bonus) else 0

        feature_rows.append(
            {
                "GameFamily": game_family,
                "GameName": game_name,
                "DrawType": draw_type,
                "DrawDate": draw_date,
                "DrawDay": row.get("DrawDay"),
                "DrawNumber": row.get("DrawNumber"),
                "N1": row.get("N1"),
                "N2": row.get("N2"),
                "N3": row.get("N3"),
                "N4": row.get("N4"),
                "N5": row.get("N5"),
                "N6": row.get("N6"),
                "Bonus": bonus,
                "NumberCount": number_count,
                "RegularSum": regular_sum,
                "AverageNumber": round(regular_sum / number_count, 2),
                "MinNumber": min_regular,
                "MaxNumber": max_regular,
                "NumberSpread": max_regular - min_regular,
                "OddCount": odd_count(numbers),
                "EvenCount": even_count(numbers),
                "LowCount": lows,
                "HighCount": highs,
                "LowThresholdUsed": low_threshold,
                "RegularRange": regular_range,
                "BonusRange": bonus_range,
                "ConsecutivePairs": count_consecutive_pairs(numbers),
                "AverageGap": round(sum(gaps) / len(gaps), 2) if gaps else 0,
                "MinGap": min(gaps) if gaps else 0,
                "MaxGap": max(gaps) if gaps else 0,
                "HasBonus": has_bonus,
                "SourceName": row.get("SourceName", ""),
                "SourceUrl": row.get("SourceUrl", ""),
                "RecordKey": row.get("RecordKey", ""),
            }
        )

    features = pd.DataFrame(feature_rows)

    if features.empty:
        return features

    features = features.sort_values(
        by=["GameFamily", "GameName", "DrawType", "DrawDate"],
        ascending=[True, True, True, False],
    ).reset_index(drop=True)

    return features


# =========================================================
# SQLITE EXPORT
# =========================================================


def export_base_features() -> pd.DataFrame:
    df = load_lottery_history()
    features = add_base_features(df)

    rows = replace_sqlite_table(BASE_FEATURES_TABLE, features)
    create_indexes(BASE_FEATURES_TABLE, ["GameFamily", "GameName", "DrawDate", "DrawType"])

    print("\nBase lottery features saved to SQLite.")
    print(f"Table: {BASE_FEATURES_TABLE}")
    print(f"Rows : {rows}")

    return features


if __name__ == "__main__":
    export_base_features()
