from __future__ import annotations

import pandas as pd

from src.data.sqlite_store import replace_sqlite_table, create_indexes
from src.lottery.features.base_lottery_features import load_lottery_history, add_base_features


UK49S_FEATURES_TABLE = "lottery_uk49s_features"


def add_uk49s_features(df: pd.DataFrame) -> pd.DataFrame:
    features = add_base_features(df)
    features = features[features["GameFamily"] == "UK49s"].copy()

    if features.empty:
        return features

    features["IsLunchtime"] = (features["DrawType"] == "Lunchtime").astype(int)
    features["IsTeatime"] = (features["DrawType"] == "Teatime").astype(int)
    features["RegularRange"] = "1-49"
    features["BonusRange"] = "1-49"

    features["BonusLowHigh"] = features["Bonus"].apply(
        lambda x: "None" if pd.isna(x) else ("Low" if int(x) <= 24 else "High")
    )
    features["BonusOddEven"] = features["Bonus"].apply(
        lambda x: "None" if pd.isna(x) else ("Odd" if int(x) % 2 != 0 else "Even")
    )

    features["RegularStructure"] = (
        features["HighCount"].astype(str) + "H-" + features["LowCount"].astype(str) + "L"
    )

    features["OddEvenStructure"] = (
        features["OddCount"].astype(str) + "O-" + features["EvenCount"].astype(str) + "E"
    )

    features["SumBand"] = pd.cut(
        features["RegularSum"],
        bins=[0, 120, 170, 230, 300],
        labels=["Low Sum", "Mid Sum", "High Sum", "Extreme Sum"],
        include_lowest=True,
    )

    features["SpreadBand"] = pd.cut(
        features["NumberSpread"],
        bins=[0, 15, 25, 38, 49],
        labels=["Tight", "Balanced", "Wide", "Extreme"],
        include_lowest=True,
    )

    features["HasConsecutive"] = (features["ConsecutivePairs"] > 0).astype(int)
    features["ConsecutiveCategory"] = pd.cut(
        features["ConsecutivePairs"],
        bins=[-1, 0, 1, 6],
        labels=["None", "Light", "Heavy"],
    )

    features["IsWeekendDraw"] = features["DrawDay"].isin(["Saturday", "Sunday"]).astype(int)
    features["IsWeekdayDraw"] = (features["IsWeekendDraw"] == 0).astype(int)

    features = features.sort_values(by=["DrawDate", "DrawType"], ascending=[False, True]).reset_index(drop=True)
    features["HistoricalSequence"] = features.index + 1

    return features


def export_uk49s_features() -> pd.DataFrame:
    df = load_lottery_history()
    features = add_uk49s_features(df)

    rows = replace_sqlite_table(UK49S_FEATURES_TABLE, features)
    create_indexes(UK49S_FEATURES_TABLE, ["GameFamily", "GameName", "DrawType", "DrawDate"])

    print("\nUK49s features saved to SQLite.")
    print(f"Table: {UK49S_FEATURES_TABLE}")
    print(f"Rows : {rows}")

    return features


if __name__ == "__main__":
    export_uk49s_features()
