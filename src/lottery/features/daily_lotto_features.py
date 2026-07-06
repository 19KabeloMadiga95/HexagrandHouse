from __future__ import annotations

import pandas as pd

from src.data.sqlite_store import replace_sqlite_table, create_indexes
from src.lottery.features.base_lottery_features import load_lottery_history, add_base_features


DAILY_LOTTO_FEATURES_TABLE = "lottery_daily_lotto_features"


def add_daily_lotto_features(df: pd.DataFrame) -> pd.DataFrame:
    features = add_base_features(df)
    features = features[features["GameFamily"] == "Daily Lotto"].copy()

    if features.empty:
        return features

    features["IsDailyLotto"] = 1
    features["RegularRange"] = "1-36"
    features["BonusRange"] = "None"

    features["RegularStructure"] = (
        features["HighCount"].astype(str) + "H-" + features["LowCount"].astype(str) + "L"
    )

    features["OddEvenStructure"] = (
        features["OddCount"].astype(str) + "O-" + features["EvenCount"].astype(str) + "E"
    )

    features["SumBand"] = pd.cut(
        features["RegularSum"],
        bins=[0, 60, 95, 130, 180],
        labels=["Low Sum", "Mid Sum", "High Sum", "Extreme Sum"],
        include_lowest=True,
    )

    features["SpreadBand"] = pd.cut(
        features["NumberSpread"],
        bins=[0, 10, 18, 28, 36],
        labels=["Tight", "Balanced", "Wide", "Extreme"],
        include_lowest=True,
    )

    features["HasConsecutive"] = (features["ConsecutivePairs"] > 0).astype(int)
    features["ConsecutiveCategory"] = pd.cut(
        features["ConsecutivePairs"],
        bins=[-1, 0, 1, 5],
        labels=["None", "Light", "Heavy"],
    )

    features["IsWeekendDraw"] = features["DrawDay"].isin(["Saturday", "Sunday"]).astype(int)
    features["IsWeekdayDraw"] = (features["IsWeekendDraw"] == 0).astype(int)

    features = features.sort_values(by=["DrawDate"], ascending=False).reset_index(drop=True)
    features["HistoricalSequence"] = features.index + 1

    return features


def export_daily_lotto_features() -> pd.DataFrame:
    df = load_lottery_history()
    features = add_daily_lotto_features(df)

    rows = replace_sqlite_table(DAILY_LOTTO_FEATURES_TABLE, features)
    create_indexes(DAILY_LOTTO_FEATURES_TABLE, ["GameFamily", "GameName", "DrawDate"])

    print("\nDaily Lotto features saved to SQLite.")
    print(f"Table: {DAILY_LOTTO_FEATURES_TABLE}")
    print(f"Rows : {rows}")

    return features


if __name__ == "__main__":
    export_daily_lotto_features()
