from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.lottery.config.lottery_game_rules import (
    get_current_rule,
    get_prediction_regular_range,
    get_prediction_bonus_range,
    get_max_historical_regular_number,
    get_max_historical_bonus_number,
)


BASE_DIR = Path(__file__).resolve().parents[3]
FEATURES_FILE = BASE_DIR / "data" / "processed" / "features" / "lotto_features.xlsx"
EXPORT_DIR = BASE_DIR / "data" / "exports" / "backtesting"
OUTPUT_FILE = EXPORT_DIR / "lotto_backtest_results.xlsx"

GAME_NAME = "Lotto"
CURRENT_RULE = get_current_rule(GAME_NAME)
PREDICTION_REGULAR_RANGE = get_prediction_regular_range(GAME_NAME)
PREDICTION_BONUS_RANGE = get_prediction_bonus_range(GAME_NAME)
HISTORICAL_REGULAR_RANGE = range(1, get_max_historical_regular_number(GAME_NAME) + 1)
_historical_bonus_max = get_max_historical_bonus_number(GAME_NAME)
HISTORICAL_BONUS_RANGE = range(1, _historical_bonus_max + 1) if _historical_bonus_max else None

TEST_DRAWS = 100
PREDICTIONS_PER_DRAW = 10
REGULAR_PICK_COUNT = CURRENT_RULE.regular_pick_count
HAS_BONUS = PREDICTION_BONUS_RANGE is not None and CURRENT_RULE.bonus_pick_count > 0
REGULAR_COLS = [f"N{i}" for i in range(1, REGULAR_PICK_COUNT + 1)]
BONUS_COL = "Bonus"
RNG_SEED = 42
_rng = np.random.default_rng(RNG_SEED)

MIN_REGULAR_SUM = int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT * 0.25)
MAX_REGULAR_SUM = int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT * 0.95)


def load_lotto_features(game_name=GAME_NAME) -> pd.DataFrame:
    if not FEATURES_FILE.exists():
        raise FileNotFoundError(
            f"Lotto features file not found:\n{FEATURES_FILE}\n\n"
            "Run this first:\npython -m src.lottery.features.lotto_features"
        )

    df = pd.read_excel(FEATURES_FILE, sheet_name="Lotto_Features", engine="openpyxl")
    df["DrawDate"] = pd.to_datetime(df["DrawDate"], errors="coerce")

    number_cols = REGULAR_COLS + ([BONUS_COL] if BONUS_COL in df.columns else [])
    for col in number_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["DrawDate"] + REGULAR_COLS)
    if "GameName" in df.columns:
        df = df[df["GameName"].astype(str).str.strip().str.lower() == game_name.lower()].copy()

    return df.sort_values(by="DrawDate", ascending=False).reset_index(drop=True)


def get_regular_list(row) -> list[int]:
    return [int(row[col]) for col in REGULAR_COLS if col in row and pd.notna(row[col])]


def get_regular_set(row) -> set[int]:
    return set(get_regular_list(row))


def get_bonus_value(row) -> int | None:
    if BONUS_COL not in row or pd.isna(row[BONUS_COL]):
        return None
    return int(row[BONUS_COL])


def build_weighted_number_pool(train_df):
    regular_counts = {n: 1.0 for n in HISTORICAL_REGULAR_RANGE}
    bonus_counts = {n: 1.0 for n in HISTORICAL_BONUS_RANGE} if HISTORICAL_BONUS_RANGE is not None else {}

    for idx, row in train_df.iterrows():
        recency_weight = 0.985 ** idx
        for n in get_regular_list(row):
            if n in regular_counts:
                regular_counts[n] += recency_weight

        bonus = get_bonus_value(row)
        if bonus is not None and bonus in bonus_counts:
            bonus_counts[bonus] += recency_weight

    # Prediction pool only contains current legal numbers.
    regular_counts = {n: regular_counts.get(n, 1.0) for n in PREDICTION_REGULAR_RANGE}
    regular_total = sum(regular_counts.values())
    regular_probs = {n: regular_counts[n] / regular_total for n in regular_counts}

    if HAS_BONUS:
        bonus_counts = {n: bonus_counts.get(n, 1.0) for n in PREDICTION_BONUS_RANGE}
        bonus_total = sum(bonus_counts.values())
        bonus_probs = {n: bonus_counts[n] / bonus_total for n in bonus_counts}
    else:
        bonus_probs = {}

    return regular_probs, bonus_probs


def weighted_sample_without_replacement(pool_probs, k):
    numbers = np.array(list(pool_probs.keys()), dtype=int)
    probs = np.array(list(pool_probs.values()), dtype=float)
    probs = probs / probs.sum()
    selected = _rng.choice(numbers, size=k, replace=False, p=probs)
    return sorted(selected.tolist())


def generate_model_predictions(train_df, prediction_count=PREDICTIONS_PER_DRAW):
    regular_probs, bonus_probs = build_weighted_number_pool(train_df)
    predictions = []
    seen = set()
    attempts = 0
    max_attempts = prediction_count * 150

    while len(predictions) < prediction_count and attempts < max_attempts:
        attempts += 1
        regulars = weighted_sample_without_replacement(regular_probs, k=REGULAR_PICK_COUNT)

        if HAS_BONUS:
            bonus_pool = {n: bonus_probs[n] for n in PREDICTION_BONUS_RANGE if n not in regulars}
            bonus = weighted_sample_without_replacement(bonus_pool, k=1)[0]
        else:
            bonus = None

        regular_sum = sum(regulars)
        if regular_sum < MIN_REGULAR_SUM or regular_sum > MAX_REGULAR_SUM:
            continue

        key = tuple(regulars + ([bonus] if HAS_BONUS else []))
        if key in seen:
            continue
        seen.add(key)

        row = {f"N{i + 1}": regulars[i] for i in range(REGULAR_PICK_COUNT)}
        row["RegularSum"] = regular_sum
        if HAS_BONUS:
            row["Bonus"] = bonus
        predictions.append(row)

    return pd.DataFrame(predictions)


def generate_random_predictions(prediction_count=PREDICTIONS_PER_DRAW):
    predictions = []
    seen = set()

    while len(predictions) < prediction_count:
        regulars = sorted(_rng.choice(list(PREDICTION_REGULAR_RANGE), size=REGULAR_PICK_COUNT, replace=False).tolist())

        if HAS_BONUS:
            bonus_pool = [n for n in PREDICTION_BONUS_RANGE if n not in regulars]
            bonus = int(_rng.choice(bonus_pool, size=1)[0])
        else:
            bonus = None

        key = tuple(regulars + ([bonus] if HAS_BONUS else []))
        if key in seen:
            continue
        seen.add(key)

        row = {f"N{i + 1}": regulars[i] for i in range(REGULAR_PICK_COUNT)}
        row["RegularSum"] = sum(regulars)
        if HAS_BONUS:
            row["Bonus"] = bonus
        predictions.append(row)

    return pd.DataFrame(predictions)


def score_predictions(predictions_df, actual_row, model_name):
    actual_regulars = get_regular_set(actual_row)
    actual_bonus = get_bonus_value(actual_row)
    rows = []

    for rank, pred in predictions_df.reset_index(drop=True).iterrows():
        predicted_regulars = set(int(pred[col]) for col in REGULAR_COLS if col in pred and pd.notna(pred[col]))
        regular_matches = len(predicted_regulars.intersection(actual_regulars))

        if HAS_BONUS and actual_bonus is not None and BONUS_COL in pred and pd.notna(pred[BONUS_COL]):
            bonus_match = 1 if int(pred[BONUS_COL]) == actual_bonus else 0
        else:
            bonus_match = 0

        rows.append({
            "ModelName": model_name,
            "PredictionRank": rank + 1,
            "ActualDrawDate": actual_row["DrawDate"],
            "ActualNumbers": ",".join(map(str, sorted(actual_regulars))),
            "ActualBonus": actual_bonus,
            "PredictedNumbers": ",".join(map(str, sorted(predicted_regulars))),
            "PredictedBonus": int(pred[BONUS_COL]) if HAS_BONUS and BONUS_COL in pred and pd.notna(pred[BONUS_COL]) else None,
            "RegularMatches": regular_matches,
            "BonusMatch": bonus_match,
            "TotalScore": regular_matches + bonus_match,
            "RuleVersion": CURRENT_RULE.rule_version,
        })

    return rows


def run_lotto_backtest(game_name=GAME_NAME, test_draws=TEST_DRAWS, predictions_per_draw=PREDICTIONS_PER_DRAW):
    df = load_lotto_features(game_name=game_name)
    if len(df) <= test_draws + 20:
        raise ValueError(f"Not enough rows to backtest. Rows available: {len(df)}")

    results = []
    max_test_index = min(test_draws, len(df) - 20)

    print("\n======================================")
    print("LOTTO BACKTEST")
    print("======================================")
    print(f"GameName             : {game_name}")
    print(f"Historical rows       : {len(df)}")
    print(f"Test draws            : {max_test_index}")
    print(f"Predictions per draw  : {predictions_per_draw}")
    print(f"Prediction rule       : {CURRENT_RULE.rule_version}")
    print("======================================\n")

    for test_idx in range(max_test_index):
        actual_row = df.iloc[test_idx]
        train_df = df.iloc[test_idx + 1:].copy()

        model_predictions = generate_model_predictions(train_df=train_df, prediction_count=predictions_per_draw)
        random_predictions = generate_random_predictions(prediction_count=predictions_per_draw)

        results.extend(score_predictions(model_predictions, actual_row, "Lotto_v3_rules_aware"))
        results.extend(score_predictions(random_predictions, actual_row, "Random_Baseline"))

        if (test_idx + 1) % 10 == 0:
            print(f"Completed {test_idx + 1} / {max_test_index} test draws...")

    return pd.DataFrame(results)


def build_backtest_summary(results_df):
    rows = []
    for model_name, group in results_df.groupby("ModelName"):
        draw_group = group.groupby("ActualDrawDate")
        best_per_draw = draw_group["TotalScore"].max()
        best_regular_per_draw = draw_group["RegularMatches"].max()
        bonus_hit_per_draw = draw_group["BonusMatch"].max()
        rows.append({
            "ModelName": model_name,
            "PredictionRows": len(group),
            "DrawsTested": group["ActualDrawDate"].nunique(),
            "AverageRegularMatches_AllRows": round(group["RegularMatches"].mean(), 4),
            "AverageTotalScore_AllRows": round(group["TotalScore"].mean(), 4),
            "BestRegularMatch_AnyRow": int(group["RegularMatches"].max()),
            "BestTotalScore_AnyRow": int(group["TotalScore"].max()),
            "AverageBestScore_PerDraw": round(best_per_draw.mean(), 4),
            "AverageBestRegularMatch_PerDraw": round(best_regular_per_draw.mean(), 4),
            "DrawsWithAtLeast2RegularMatches": int((best_regular_per_draw >= 2).sum()),
            "DrawsWithAtLeast3RegularMatches": int((best_regular_per_draw >= 3).sum()),
            "DrawsWithBonusHit": int((bonus_hit_per_draw >= 1).sum()),
            "BonusHitDrawRate": round((bonus_hit_per_draw >= 1).mean(), 4),
        })
    return pd.DataFrame(rows)


def build_rank_summary(results_df):
    return results_df.groupby(["ModelName", "PredictionRank"]).agg(
        PredictionRows=("TotalScore", "count"),
        AvgRegularMatches=("RegularMatches", "mean"),
        AvgTotalScore=("TotalScore", "mean"),
        MaxRegularMatches=("RegularMatches", "max"),
        MaxTotalScore=("TotalScore", "max"),
        BonusHitRate=("BonusMatch", "mean"),
    ).reset_index()


def export_lotto_backtest(game_name=GAME_NAME, test_draws=TEST_DRAWS, predictions_per_draw=PREDICTIONS_PER_DRAW):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    results_df = run_lotto_backtest(game_name=game_name, test_draws=test_draws, predictions_per_draw=predictions_per_draw)
    summary_df = build_backtest_summary(results_df)
    rank_summary_df = build_rank_summary(results_df)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl", mode="w") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        rank_summary_df.to_excel(writer, sheet_name="Rank_Summary", index=False)
        results_df.to_excel(writer, sheet_name="Detailed_Results", index=False)

    print("\nLotto backtest exported.")
    print(f"Rows: {len(results_df)}")
    print(f"File: {OUTPUT_FILE}")
    return results_df, summary_df


def main():
    export_lotto_backtest(game_name=GAME_NAME, test_draws=TEST_DRAWS, predictions_per_draw=PREDICTIONS_PER_DRAW)


if __name__ == "__main__":
    main()
