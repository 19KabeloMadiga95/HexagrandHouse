from __future__ import annotations

from pathlib import Path
from collections import Counter
from itertools import combinations

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
OUTPUT_FILE = EXPORT_DIR / "lotto_model_comparison_backtest.xlsx"

GAME_NAME = "Lotto"
CURRENT_RULE = get_current_rule(GAME_NAME)
PREDICTION_REGULAR_RANGE = get_prediction_regular_range(GAME_NAME)
PREDICTION_BONUS_RANGE = get_prediction_bonus_range(GAME_NAME)
HISTORICAL_REGULAR_RANGE = range(1, get_max_historical_regular_number(GAME_NAME) + 1)
_historical_bonus_max = get_max_historical_bonus_number(GAME_NAME)
HISTORICAL_BONUS_RANGE = range(1, _historical_bonus_max + 1) if _historical_bonus_max else None

REGULAR_PICK_COUNT = CURRENT_RULE.regular_pick_count
HAS_BONUS = PREDICTION_BONUS_RANGE is not None and CURRENT_RULE.bonus_pick_count > 0
REGULAR_COLS = [f"N{i}" for i in range(1, REGULAR_PICK_COUNT + 1)]
BONUS_COL = "Bonus"

TEST_DRAWS = 100
PREDICTIONS_PER_DRAW = 10
RNG_SEED = 42
_rng = np.random.default_rng(RNG_SEED)

LOW_HIGH_MIDPOINT = CURRENT_RULE.regular_max // 2
MIN_REGULAR_SUM = int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT * 0.25)
MAX_REGULAR_SUM = int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT * 0.95)

MODEL_CONFIGS = [
    {"ModelName": "Random_Baseline", "Mode": "random", "LookbackWindow": None, "FrequencyWeight": 0.0, "RecencyWeight": 0.0, "OverdueWeight": 0.0, "PairWeight": 0.0, "HybridRandomness": 1.0, "PenaltyHotCluster": 0.0},
    {"ModelName": "Weighted_AllHistory_v3", "Mode": "weighted", "LookbackWindow": None, "FrequencyWeight": 2.5, "RecencyWeight": 1.5, "OverdueWeight": 1.0, "PairWeight": 0.8, "HybridRandomness": 0.0, "PenaltyHotCluster": 0.0},
    {"ModelName": "Weighted_Recent100_v3", "Mode": "weighted", "LookbackWindow": 100, "FrequencyWeight": 2.0, "RecencyWeight": 2.2, "OverdueWeight": 0.8, "PairWeight": 0.5, "HybridRandomness": 0.0, "PenaltyHotCluster": 0.0},
    {"ModelName": "Hybrid_70Weighted_30Random_v3", "Mode": "hybrid", "LookbackWindow": 100, "FrequencyWeight": 2.0, "RecencyWeight": 2.0, "OverdueWeight": 0.7, "PairWeight": 0.4, "HybridRandomness": 0.30, "PenaltyHotCluster": 0.2},
    {"ModelName": "Hybrid_50Weighted_50Random_v3", "Mode": "hybrid", "LookbackWindow": 100, "FrequencyWeight": 1.5, "RecencyWeight": 1.5, "OverdueWeight": 0.5, "PairWeight": 0.2, "HybridRandomness": 0.50, "PenaltyHotCluster": 0.3},
    {"ModelName": "AntiCrowding_Recent100_v3", "Mode": "weighted", "LookbackWindow": 100, "FrequencyWeight": 1.5, "RecencyWeight": 2.0, "OverdueWeight": 1.0, "PairWeight": 0.2, "HybridRandomness": 0.15, "PenaltyHotCluster": 0.6},
]


def load_lotto_features(game_name=GAME_NAME):
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


def normalise_01(series):
    series = pd.Series(series, dtype=float)
    lo = series.min()
    hi = series.max()
    if hi <= lo:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)


def get_regular_list(row):
    return [int(row[col]) for col in REGULAR_COLS if col in row and pd.notna(row[col])]


def get_regular_set(row):
    return set(get_regular_list(row))


def get_bonus_value(row):
    if BONUS_COL not in row or pd.isna(row[BONUS_COL]):
        return None
    return int(row[BONUS_COL])


def count_consecutive(numbers):
    numbers = sorted(numbers)
    return sum(1 for i in range(len(numbers) - 1) if numbers[i + 1] - numbers[i] == 1)


def count_high_low(numbers):
    low = sum(1 for n in numbers if n <= LOW_HIGH_MIDPOINT)
    return len(numbers) - low, low


def count_odd_even(numbers):
    odd = sum(1 for n in numbers if n % 2 != 0)
    return odd, len(numbers) - odd


def weighted_choice_no_replace(pool, weights, k):
    pool = np.array(list(pool), dtype=int)
    weights = np.array(list(weights), dtype=float)
    probs = np.ones(len(pool)) / len(pool) if weights.sum() <= 0 else weights / weights.sum()
    return sorted(_rng.choice(pool, size=k, replace=False, p=probs).tolist())


def apply_lookback(train_df, lookback_window):
    return train_df.copy() if lookback_window is None else train_df.head(lookback_window).copy()


def build_frequency_scores(train_df):
    reg_counter = Counter()
    bonus_counter = Counter()

    for _, row in train_df.iterrows():
        for n in get_regular_list(row):
            if n in HISTORICAL_REGULAR_RANGE:
                reg_counter[n] += 1

        bonus = get_bonus_value(row)
        if bonus is not None and HISTORICAL_BONUS_RANGE is not None and bonus in HISTORICAL_BONUS_RANGE:
            bonus_counter[bonus] += 1

    reg_scores = pd.Series({n: reg_counter[n] for n in HISTORICAL_REGULAR_RANGE})
    bonus_scores = pd.Series({n: bonus_counter[n] for n in HISTORICAL_BONUS_RANGE}) if HISTORICAL_BONUS_RANGE is not None else pd.Series(dtype=float)
    return normalise_01(reg_scores), normalise_01(bonus_scores)


def build_recency_scores(train_df, decay=0.985):
    reg_scores = pd.Series(0.0, index=pd.Index(HISTORICAL_REGULAR_RANGE), dtype=float)
    bonus_scores = pd.Series(0.0, index=pd.Index(HISTORICAL_BONUS_RANGE), dtype=float) if HISTORICAL_BONUS_RANGE is not None else pd.Series(dtype=float)

    for idx, row in train_df.iterrows():
        weight = decay ** idx
        for n in get_regular_list(row):
            if n in reg_scores.index:
                reg_scores.loc[n] += weight

        bonus = get_bonus_value(row)
        if bonus is not None and not bonus_scores.empty and bonus in bonus_scores.index:
            bonus_scores.loc[bonus] += weight

    return normalise_01(reg_scores), normalise_01(bonus_scores)


def build_overdue_scores(train_df):
    last_seen = {n: None for n in HISTORICAL_REGULAR_RANGE}
    for idx, row in train_df.iterrows():
        for n in get_regular_list(row):
            if n in last_seen and last_seen[n] is None:
                last_seen[n] = idx
    scores = {n: (len(train_df) if last_seen[n] is None else last_seen[n]) for n in HISTORICAL_REGULAR_RANGE}
    return normalise_01(pd.Series(scores))


def build_pair_scores(train_df):
    pair_counter = Counter()
    for _, row in train_df.iterrows():
        numbers = sorted(n for n in get_regular_list(row) if n in HISTORICAL_REGULAR_RANGE)
        for pair in combinations(numbers, 2):
            pair_counter[pair] += 1
    return pair_counter


def build_number_weights(train_df, config):
    freq_reg, freq_bonus = build_frequency_scores(train_df)
    rec_reg, rec_bonus = build_recency_scores(train_df)
    overdue_reg = build_overdue_scores(train_df)

    reg_weights_all = config["FrequencyWeight"] * freq_reg + config["RecencyWeight"] * rec_reg + config["OverdueWeight"] * overdue_reg
    reg_weights = reg_weights_all.reindex(list(PREDICTION_REGULAR_RANGE)).fillna(0.001).clip(lower=0.001)

    if HAS_BONUS:
        bonus_weights_all = config["FrequencyWeight"] * freq_bonus + config["RecencyWeight"] * rec_bonus
        bonus_weights = bonus_weights_all.reindex(list(PREDICTION_BONUS_RANGE)).fillna(0.001).clip(lower=0.001)
    else:
        bonus_weights = pd.Series(dtype=float)

    return reg_weights.to_dict(), bonus_weights.to_dict()


def build_hot_numbers(train_df, top_n=12):
    counter = Counter()
    for _, row in train_df.iterrows():
        for n in get_regular_list(row):
            if n in PREDICTION_REGULAR_RANGE:
                counter[n] += 1
    return set([n for n, _ in counter.most_common(top_n)])


def score_pair_strength(numbers, pair_counter):
    return sum(pair_counter[pair] for pair in combinations(sorted(numbers), 2))


def score_pattern(numbers):
    high, low = count_high_low(numbers)
    odd, even = count_odd_even(numbers)
    total = sum(numbers)
    consecutive = count_consecutive(numbers)
    score = 0

    if (high, low) in [(3, 3), (4, 2), (2, 4)]:
        score += 4
    elif (high, low) in [(5, 1), (1, 5)]:
        score += 1

    if (odd, even) in [(3, 3), (4, 2), (2, 4)]:
        score += 4
    elif (odd, even) in [(5, 1), (1, 5)]:
        score += 1

    if MIN_REGULAR_SUM <= total <= MAX_REGULAR_SUM:
        score += 4
    elif int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT * 0.22) <= total <= int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT):
        score += 2

    if consecutive <= 1:
        score += 3
    elif consecutive == 2:
        score += 1
    return score


def hot_cluster_penalty(numbers, hot_numbers):
    return sum(1 for n in numbers if n in hot_numbers)


def passes_basic_filters(numbers):
    total = sum(numbers)
    if total < MIN_REGULAR_SUM or total > MAX_REGULAR_SUM:
        return False
    if count_consecutive(numbers) > 3:
        return False
    return True


def generate_random_predictions(prediction_count):
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
        row["ModelRawScore"] = 0
        if HAS_BONUS:
            row["Bonus"] = bonus
        predictions.append(row)

    return pd.DataFrame(predictions)


def generate_weighted_predictions(train_df, config, prediction_count):
    model_train_df = apply_lookback(train_df, config["LookbackWindow"])
    reg_weights, bonus_weights = build_number_weights(model_train_df, config)
    pair_counter = build_pair_scores(model_train_df)
    hot_numbers = build_hot_numbers(model_train_df, top_n=12)

    candidates = []
    seen = set()
    attempts = 0
    max_attempts = prediction_count * 600

    while len(candidates) < prediction_count * 50 and attempts < max_attempts:
        attempts += 1
        hybrid_randomness = config["HybridRandomness"]

        if config["Mode"] == "hybrid" and _rng.random() < hybrid_randomness:
            regulars = sorted(_rng.choice(list(PREDICTION_REGULAR_RANGE), size=REGULAR_PICK_COUNT, replace=False).tolist())
        else:
            regulars = weighted_choice_no_replace(
                pool=list(PREDICTION_REGULAR_RANGE),
                weights=[reg_weights[n] for n in PREDICTION_REGULAR_RANGE],
                k=REGULAR_PICK_COUNT,
            )

        if HAS_BONUS:
            if _rng.random() < hybrid_randomness:
                bonus_pool = [n for n in PREDICTION_BONUS_RANGE if n not in regulars]
                bonus = int(_rng.choice(bonus_pool, size=1)[0])
            else:
                bonus_pool = {n: bonus_weights[n] for n in PREDICTION_BONUS_RANGE if n not in regulars}
                bonus = weighted_choice_no_replace(pool=list(bonus_pool.keys()), weights=list(bonus_pool.values()), k=1)[0]
        else:
            bonus = None

        key = tuple(regulars + ([bonus] if HAS_BONUS else []))
        if key in seen or not passes_basic_filters(regulars):
            continue
        seen.add(key)

        base_score = sum(reg_weights[n] for n in regulars)
        if HAS_BONUS:
            base_score += bonus_weights[bonus]

        raw_score = (
            base_score
            + config["PairWeight"] * score_pair_strength(regulars, pair_counter)
            + score_pattern(regulars)
            - config["PenaltyHotCluster"] * hot_cluster_penalty(regulars, hot_numbers)
        )

        row = {f"N{i + 1}": regulars[i] for i in range(REGULAR_PICK_COUNT)}
        row["RegularSum"] = sum(regulars)
        row["ModelRawScore"] = raw_score
        if HAS_BONUS:
            row["Bonus"] = bonus
        candidates.append(row)

    if not candidates:
        return generate_random_predictions(prediction_count)

    candidates_df = pd.DataFrame(candidates).sort_values(by="ModelRawScore", ascending=False).reset_index(drop=True)
    selected = []

    for _, row in candidates_df.iterrows():
        candidate = [int(row[col]) for col in REGULAR_COLS]
        if HAS_BONUS:
            candidate.append(int(row["Bonus"]))
        candidate_set = set(candidate[:REGULAR_PICK_COUNT])
        ok = True
        for existing in selected:
            if len(candidate_set.intersection(set(existing[:REGULAR_PICK_COUNT]))) > 4:
                ok = False
                break
        if ok:
            selected.append(candidate)
        if len(selected) >= prediction_count:
            break

    final_rows = []
    for candidate in selected:
        row = {f"N{i + 1}": candidate[i] for i in range(REGULAR_PICK_COUNT)}
        row["RegularSum"] = sum(candidate[:REGULAR_PICK_COUNT])
        row["ModelRawScore"] = 0
        if HAS_BONUS:
            row["Bonus"] = candidate[-1]
        final_rows.append(row)
    return pd.DataFrame(final_rows)


def generate_predictions_for_model(train_df, config, prediction_count):
    if config["Mode"] == "random":
        return generate_random_predictions(prediction_count)
    return generate_weighted_predictions(train_df=train_df, config=config, prediction_count=prediction_count)


def score_predictions(predictions_df, actual_row, model_name):
    actual_regulars = get_regular_set(actual_row)
    actual_bonus = get_bonus_value(actual_row)
    rows = []

    for rank, pred in predictions_df.reset_index(drop=True).iterrows():
        predicted_regulars = set(int(pred[col]) for col in REGULAR_COLS if col in pred and pd.notna(pred[col]))
        regular_matches = len(predicted_regulars.intersection(actual_regulars))
        bonus_match = 0
        if HAS_BONUS and actual_bonus is not None and BONUS_COL in pred and pd.notna(pred[BONUS_COL]):
            bonus_match = 1 if int(pred[BONUS_COL]) == actual_bonus else 0

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


def run_lotto_model_comparison_backtest(game_name=GAME_NAME, test_draws=TEST_DRAWS, predictions_per_draw=PREDICTIONS_PER_DRAW):
    df = load_lotto_features(game_name=game_name)
    if len(df) <= test_draws + 20:
        raise ValueError(f"Not enough rows to backtest. Rows available: {len(df)}")

    results = []
    max_test_index = min(test_draws, len(df) - 20)

    print("\n======================================")
    print("LOTTO MODEL COMPARISON BACKTEST")
    print("======================================")
    print(f"GameName             : {game_name}")
    print(f"Historical rows       : {len(df)}")
    print(f"Test draws            : {max_test_index}")
    print(f"Predictions per draw  : {predictions_per_draw}")
    print(f"Models tested         : {len(MODEL_CONFIGS)}")
    print(f"Prediction rule       : {CURRENT_RULE.rule_version}")
    print("======================================\n")

    for test_idx in range(max_test_index):
        actual_row = df.iloc[test_idx]
        train_df = df.iloc[test_idx + 1:].copy()
        for config in MODEL_CONFIGS:
            predictions = generate_predictions_for_model(train_df=train_df, config=config, prediction_count=predictions_per_draw)
            results.extend(score_predictions(predictions_df=predictions, actual_row=actual_row, model_name=config["ModelName"]))
        if (test_idx + 1) % 10 == 0:
            print(f"Completed {test_idx + 1} / {max_test_index} test draws...")

    return pd.DataFrame(results)


def build_model_summary(results_df):
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
    summary = pd.DataFrame(rows)
    summary = summary.sort_values(by=["AverageBestRegularMatch_PerDraw", "DrawsWithAtLeast3RegularMatches", "AverageTotalScore_AllRows"], ascending=[False, False, False]).reset_index(drop=True)
    summary["Rank"] = summary.index + 1
    return summary


def build_rank_summary(results_df):
    return results_df.groupby(["ModelName", "PredictionRank"]).agg(
        PredictionRows=("TotalScore", "count"),
        AvgRegularMatches=("RegularMatches", "mean"),
        AvgTotalScore=("TotalScore", "mean"),
        MaxRegularMatches=("RegularMatches", "max"),
        MaxTotalScore=("TotalScore", "max"),
        BonusHitRate=("BonusMatch", "mean"),
    ).reset_index()


def build_hit_distribution(results_df):
    return results_df.groupby(["ModelName", "RegularMatches"]).agg(Count=("RegularMatches", "count")).reset_index()


def export_lotto_model_comparison_backtest(game_name=GAME_NAME, test_draws=TEST_DRAWS, predictions_per_draw=PREDICTIONS_PER_DRAW):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    results_df = run_lotto_model_comparison_backtest(game_name=game_name, test_draws=test_draws, predictions_per_draw=predictions_per_draw)
    summary_df = build_model_summary(results_df)
    rank_summary_df = build_rank_summary(results_df)
    hit_distribution_df = build_hit_distribution(results_df)
    config_df = pd.DataFrame(MODEL_CONFIGS)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl", mode="w") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        rank_summary_df.to_excel(writer, sheet_name="Rank_Summary", index=False)
        hit_distribution_df.to_excel(writer, sheet_name="Hit_Distribution", index=False)
        config_df.to_excel(writer, sheet_name="Model_Configs", index=False)
        results_df.to_excel(writer, sheet_name="Detailed_Results", index=False)

    print("\nLotto model comparison backtest exported.")
    print(f"Rows: {len(results_df)}")
    print(f"File: {OUTPUT_FILE}")
    return results_df, summary_df


def main():
    export_lotto_model_comparison_backtest(game_name=GAME_NAME, test_draws=TEST_DRAWS, predictions_per_draw=PREDICTIONS_PER_DRAW)


if __name__ == "__main__":
    main()
