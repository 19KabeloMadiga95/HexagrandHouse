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

OUTPUT_FILE = FEATURES_DIR / "lotto_features.xlsx"


# =========================================================
# LOTTO FEATURE ENGINE
# =========================================================

def add_lotto_features(df):
    features = add_base_features(df)

    features = features[
        features["GameFamily"] == "Lotto"
    ].copy()

    if features.empty:
        return features

    features["IsLottoMain"] = (
        features["GameName"] == "Lotto"
    ).astype(int)

    features["IsLottoPlus1"] = (
        features["GameName"] == "Lotto Plus 1"
    ).astype(int)

    features["IsLottoPlus2"] = (
        features["GameName"] == "Lotto Plus 2"
    ).astype(int)

    features["RegularRange"] = "1-58"
    features["BonusRange"] = "1-58"

    features["BonusLowHigh"] = features["Bonus"].apply(
        lambda x: "Low" if pd.notna(x) and int(x) <= 29 else "High"
    )

    features["BonusOddEven"] = features["Bonus"].apply(
        lambda x: "Odd" if pd.notna(x) and int(x) % 2 != 0 else "Even"
    )

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
        bins=[0, 120, 170, 230, 320],
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
        bins=[0, 18, 30, 45, 58],
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
        bins=[-1, 0, 1, 6],
        labels=[
            "None",
            "Light",
            "Heavy",
        ]
    )

    features["IsWednesdayDraw"] = (
        features["DrawDay"] == "Wednesday"
    ).astype(int)

    features["IsSaturdayDraw"] = (
        features["DrawDay"] == "Saturday"
    ).astype(int)

    features = features.sort_values(
        by=["DrawDate", "GameName"],
        ascending=[False, True]
    ).reset_index(drop=True)

    features["HistoricalSequence"] = (
        features.index + 1
    )

    return features


# =========================================================
# EXPORT
# =========================================================

def export_lotto_features():
    FEATURES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df = load_lottery_history()

    features = add_lotto_features(df)

    features.to_excel(
        OUTPUT_FILE,
        sheet_name="Lotto_Features",
        index=False
    )

    print("\nLotto features exported.")
    print(f"Rows: {len(features)}")
    print(f"File: {OUTPUT_FILE}")

    return features


# =========================================================
# QUICK TEST
# =========================================================

if __name__ == "__main__":
    export_lotto_features()