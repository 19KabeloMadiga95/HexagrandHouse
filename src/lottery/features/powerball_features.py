from __future__ import annotations

import pandas as pd

from src.data.sqlite_store import replace_sqlite_table, create_indexes
from src.lottery.features.base_lottery_features import load_lottery_history, add_base_features
from src.lottery.config.lottery_game_rules import get_rule_for_draw


POWERBALL_FEATURES_TABLE = "lottery_powerball_features"


def _bonus_midpoint(row: pd.Series) -> int:
    rule = get_rule_for_draw(row.get("GameName", "PowerBall"), row.get("DrawDate"))
    return (rule.bonus_max // 2) if rule and rule.bonus_max else 10


def _bonus_band(row: pd.Series) -> str:
    bonus = row.get("Bonus")
    if pd.isna(bonus):
        return "None"

    rule = get_rule_for_draw(row.get("GameName", "PowerBall"), row.get("DrawDate"))
    max_bonus = rule.bonus_max if rule and rule.bonus_max else 20
    value = int(bonus)

    if max_bonus <= 16:
        bins = [(1, 4), (5, 8), (9, 12), (13, 16)]
    else:
        bins = [(1, 5), (6, 10), (11, 15), (16, 20)]

    for low, high in bins:
        if low <= value <= high:
            return f"{low}-{high}"

    return "Out of range"


def add_powerball_features(df: pd.DataFrame) -> pd.DataFrame:
    features = add_base_features(df)
    features = features[features["GameFamily"] == "PowerBall"].copy()

    if features.empty:
        return features

    features["IsPowerBallMain"] = (features["GameName"] == "PowerBall").astype(int)
    features["IsPowerBallPlus"] = (features["GameName"] == "PowerBall Plus").astype(int)

    features["BonusLowHigh"] = features.apply(
        lambda row: "None" if pd.isna(row.get("Bonus")) else ("Low" if int(row.get("Bonus")) <= _bonus_midpoint(row) else "High"),
        axis=1,
    )
    features["BonusOddEven"] = features["Bonus"].apply(
        lambda x: "None" if pd.isna(x) else ("Odd" if int(x) % 2 != 0 else "Even")
    )
    features["BonusBand"] = features.apply(_bonus_band, axis=1)

    features["RegularStructure"] = (
        features["HighCount"].astype(str) + "H-" + features["LowCount"].astype(str) + "L"
    )

    features["OddEvenStructure"] = (
        features["OddCount"].astype(str) + "O-" + features["EvenCount"].astype(str) + "E"
    )

    features["SumBand"] = pd.cut(
        features["RegularSum"],
        bins=[0, 90, 130, 180, 250],
        labels=["Low Sum", "Mid Sum", "High Sum", "Extreme Sum"],
        include_lowest=True,
    )

    features["SpreadBand"] = pd.cut(
        features["NumberSpread"],
        bins=[0, 15, 25, 35, 50],
        labels=["Tight", "Balanced", "Wide", "Extreme"],
        include_lowest=True,
    )

    features["HasConsecutive"] = (features["ConsecutivePairs"] > 0).astype(int)
    features["ConsecutiveCategory"] = pd.cut(
        features["ConsecutivePairs"],
        bins=[-1, 0, 1, 5],
        labels=["None", "Light", "Heavy"],
    )

    features["IsTuesdayDraw"] = (features["DrawDay"] == "Tuesday").astype(int)
    features["IsFridayDraw"] = (features["DrawDay"] == "Friday").astype(int)

    features = features.sort_values(by=["DrawDate"], ascending=False).reset_index(drop=True)
    features["HistoricalSequence"] = features.index + 1

    return features


def export_powerball_features() -> pd.DataFrame:
    df = load_lottery_history()
    features = add_powerball_features(df)

    rows = replace_sqlite_table(POWERBALL_FEATURES_TABLE, features)
    create_indexes(POWERBALL_FEATURES_TABLE, ["GameFamily", "GameName", "DrawDate"])

    print("\nPowerBall features saved to SQLite.")
    print(f"Table: {POWERBALL_FEATURES_TABLE}")
    print(f"Rows : {rows}")

    return features


if __name__ == "__main__":
    export_powerball_features()
