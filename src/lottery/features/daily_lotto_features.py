from pathlib import Path

import pandas as pd

from src.lottery.features.base_lottery_features import (
    load_lottery_history,
    add_base_features,
)


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

FEATURES_DIR = BASE_DIR / "data" / "processed" / "features"

OUTPUT_FILE = FEATURES_DIR / "daily_lotto_features.xlsx"


# =========================================================
# DAILY LOTTO FEATURE ENGINE
# =========================================================

def add_daily_lotto_features(df):
    features = add_base_features(df)

    features = features[
        features["GameFamily"] == "Daily Lotto"
    ].copy()

    if features.empty:
        return features

    features["IsDailyLotto"] = 1

    features["RegularRange"] = "1-36"
    features["BonusRange"] = "None"

    features["RegularStructure"] = (
        features["HighCount"].astype(str)
        + "H-"
        + features["LowCount"].astype(str)
        + "L"
    )

    features["OddEvenStructure"] = (
        features["OddCount"].astype(str)
        + "O-"
        + features["EvenCount"].astype(str)
        + "E"
    )

    features["SumBand"] = pd.cut(
        features["RegularSum"],
        bins=[0, 60, 95, 130, 180],
        labels=[
            "Low Sum",
            "Mid Sum",
            "High Sum",
            "Extreme Sum",
        ],
        include_lowest=True
    )

    features["SpreadBand"] = pd.cut(
        features["NumberSpread"],
        bins=[0, 10, 18, 28, 36],
        labels=[
            "Tight",
            "Balanced",
            "Wide",
            "Extreme",
        ],
        include_lowest=True
    )

    features["HasConsecutive"] = (
        features["ConsecutivePairs"] > 0
    ).astype(int)

    features["ConsecutiveCategory"] = pd.cut(
        features["ConsecutivePairs"],
        bins=[-1, 0, 1, 5],
        labels=[
            "None",
            "Light",
            "Heavy",
        ]
    )

    features["IsWeekendDraw"] = features["DrawDay"].isin(
        ["Saturday", "Sunday"]
    ).astype(int)

    features["IsWeekdayDraw"] = (
        features["IsWeekendDraw"] == 0
    ).astype(int)

    features = features.sort_values(
        by=["DrawDate"],
        ascending=False
    ).reset_index(drop=True)

    features["HistoricalSequence"] = (
        features.index + 1
    )

    return features


# =========================================================
# EXPORT
# =========================================================

def export_daily_lotto_features():
    FEATURES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df = load_lottery_history()

    features = add_daily_lotto_features(df)

    features.to_excel(
        OUTPUT_FILE,
        sheet_name="Daily_Lotto_Features",
        index=False
    )

    print("\nDaily Lotto features exported.")
    print(f"Rows: {len(features)}")
    print(f"File: {OUTPUT_FILE}")

    return features


# =========================================================
# QUICK TEST
# =========================================================

if __name__ == "__main__":
    export_daily_lotto_features()