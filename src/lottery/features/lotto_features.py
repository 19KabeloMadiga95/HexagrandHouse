from __future__ import annotations

import pandas as pd

from src.data.sqlite_store import replace_sqlite_table, create_indexes
from src.lottery.features.base_lottery_features import load_lottery_history, add_base_features
from src.lottery.config.lottery_game_rules import get_rule_for_draw


LOTTO_FEATURES_TABLE = "lottery_lotto_features"


def _bonus_low_high(row: pd.Series) -> str:
    bonus = row.get("Bonus")
    if pd.isna(bonus):
        return "None"

    rule = get_rule_for_draw(row.get("GameName", "Lotto"), row.get("DrawDate"))
    midpoint = (rule.bonus_max // 2) if rule and rule.bonus_max else 26
    return "Low" if int(bonus) <= midpoint else "High"


def add_lotto_features(df: pd.DataFrame) -> pd.DataFrame:
    features = add_base_features(df)
    features = features[features["GameFamily"] == "Lotto"].copy()

    if features.empty:
        return features

    features["IsLottoMain"] = (features["GameName"] == "Lotto").astype(int)
    features["IsLottoPlus1"] = (features["GameName"] == "Lotto Plus 1").astype(int)
    features["IsLottoPlus2"] = (features["GameName"] == "Lotto Plus 2").astype(int)

    features["BonusLowHigh"] = features.apply(_bonus_low_high, axis=1)
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
        bins=[0, 120, 170, 230, 320],
        labels=["Low Sum", "Mid Sum", "High Sum", "Extreme Sum"],
        include_lowest=True,
    )

    features["SpreadBand"] = pd.cut(
        features["NumberSpread"],
        bins=[0, 18, 30, 45, 58],
        labels=["Tight", "Balanced", "Wide", "Extreme"],
        include_lowest=True,
    )

    features["HasConsecutive"] = (features["ConsecutivePairs"] > 0).astype(int)
    features["ConsecutiveCategory"] = pd.cut(
        features["ConsecutivePairs"],
        bins=[-1, 0, 1, 6],
        labels=["None", "Light", "Heavy"],
    )

    features["IsWednesdayDraw"] = (features["DrawDay"] == "Wednesday").astype(int)
    features["IsSaturdayDraw"] = (features["DrawDay"] == "Saturday").astype(int)

    features = features.sort_values(by=["DrawDate", "GameName"], ascending=[False, True]).reset_index(drop=True)
    features["HistoricalSequence"] = features.index + 1

    return features


def export_lotto_features() -> pd.DataFrame:
    df = load_lottery_history()
    features = add_lotto_features(df)

    rows = replace_sqlite_table(LOTTO_FEATURES_TABLE, features)
    create_indexes(LOTTO_FEATURES_TABLE, ["GameFamily", "GameName", "DrawDate"])

    print("\nLotto features saved to SQLite.")
    print(f"Table: {LOTTO_FEATURES_TABLE}")
    print(f"Rows : {rows}")

    return features


if __name__ == "__main__":
    export_lotto_features()
