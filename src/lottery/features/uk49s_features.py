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

OUTPUT_FILE = FEATURES_DIR / "uk49s_features.xlsx"


# =========================================================
# UK49S FEATURE ENGINE
# =========================================================

def add_uk49s_features(df):
    features = add_base_features(df)

    features = features[
        features["GameFamily"] == "UK49s"
    ].copy()

    if features.empty:
        return features

    features["IsLunchtime"] = (
        features["DrawType"] == "Lunchtime"
    ).astype(int)

    features["IsTeatime"] = (
        features["DrawType"] == "Teatime"
    ).astype(int)

    features["RegularRange"] = "1-49"
    features["BonusRange"] = "1-49"

    features["BonusLowHigh"] = features["Bonus"].apply(
        lambda x: "Low" if pd.notna(x) and int(x) <= 24 else "High"
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
        bins=[0, 120, 170, 230, 300],
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
        bins=[0, 15, 25, 38, 49],
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

    features["IsWeekendDraw"] = features["DrawDay"].isin(
        ["Saturday", "Sunday"]
    ).astype(int)

    features["IsWeekdayDraw"] = (
        features["IsWeekendDraw"] == 0
    ).astype(int)

    features = features.sort_values(
        by=["DrawDate", "DrawType"],
        ascending=[False, True]
    ).reset_index(drop=True)

    features["HistoricalSequence"] = (
        features.index + 1
    )

    return features


# =========================================================
# EXPORT
# =========================================================

def export_uk49s_features():
    FEATURES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df = load_lottery_history()

    features = add_uk49s_features(df)

    features.to_excel(
        OUTPUT_FILE,
        sheet_name="UK49s_Features",
        index=False
    )

    print("\nUK49s features exported.")
    print(f"Rows: {len(features)}")
    print(f"File: {OUTPUT_FILE}")

    return features


# =========================================================
# QUICK TEST
# =========================================================

if __name__ == "__main__":
    export_uk49s_features()