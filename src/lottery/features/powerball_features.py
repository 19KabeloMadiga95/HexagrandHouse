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

OUTPUT_FILE = FEATURES_DIR / "powerball_features.xlsx"


# =========================================================
# POWERBALL FEATURE ENGINE
# =========================================================

def add_powerball_features(df):
    """
    Build PowerBall-specific features from the
    master lottery historical dataset.
    """

    features = add_base_features(df)

    # -----------------------------------------------------
    # Filter PowerBall Family
    # -----------------------------------------------------

    features = features[
        features["GameFamily"] == "PowerBall"
    ].copy()

    if features.empty:
        return features

    # -----------------------------------------------------
    # Game Type Flags
    # -----------------------------------------------------

    features["IsPowerBallMain"] = (
        features["GameName"] == "PowerBall"
    ).astype(int)

    features["IsPowerBallPlus"] = (
        features["GameName"] == "PowerBall Plus"
    ).astype(int)

    # -----------------------------------------------------
    # PowerBall Bonus Analysis
    # -----------------------------------------------------

    features["BonusLowHigh"] = features["Bonus"].apply(
        lambda x: (
            "Low"
            if pd.notna(x) and int(x) <= 10
            else "High"
        )
    )

    features["BonusOddEven"] = features["Bonus"].apply(
        lambda x: (
            "Odd"
            if pd.notna(x) and int(x) % 2 != 0
            else "Even"
        )
    )

    features["BonusBand"] = pd.cut(
        features["Bonus"],
        bins=[0, 5, 10, 15, 20],
        labels=[
            "1-5",
            "6-10",
            "11-15",
            "16-20",
        ],
        include_lowest=True
    )

    # -----------------------------------------------------
    # Game Structure
    # -----------------------------------------------------

    features["RegularRange"] = "1-50"
    features["BonusRange"] = "1-20"

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

    # -----------------------------------------------------
    # Sum Groupings
    # -----------------------------------------------------

    features["SumBand"] = pd.cut(
        features["RegularSum"],
        bins=[0, 90, 130, 180, 250],
        labels=[
            "Low Sum",
            "Mid Sum",
            "High Sum",
            "Extreme Sum",
        ],
        include_lowest=True
    )

    # -----------------------------------------------------
    # Spread Groupings
    # -----------------------------------------------------

    features["SpreadBand"] = pd.cut(
        features["NumberSpread"],
        bins=[0, 15, 25, 35, 50],
        labels=[
            "Tight",
            "Balanced",
            "Wide",
            "Extreme",
        ],
        include_lowest=True
    )

    # -----------------------------------------------------
    # Consecutive Number Flags
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Draw Day Features
    # -----------------------------------------------------

    features["IsTuesdayDraw"] = (
        features["DrawDay"] == "Tuesday"
    ).astype(int)

    features["IsFridayDraw"] = (
        features["DrawDay"] == "Friday"
    ).astype(int)

    # -----------------------------------------------------
    # Rolling Sequence ID
    # -----------------------------------------------------

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

def export_powerball_features():
    FEATURES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df = load_lottery_history()

    features = add_powerball_features(df)

    features.to_excel(
        OUTPUT_FILE,
        sheet_name="PowerBall_Features",
        index=False
    )

    print("\nPowerBall features exported.")
    print(f"Rows: {len(features)}")
    print(f"File: {OUTPUT_FILE}")

    return features


# =========================================================
# QUICK TEST
# =========================================================

if __name__ == "__main__":
    export_powerball_features()