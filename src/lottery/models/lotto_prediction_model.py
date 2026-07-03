from __future__ import annotations

from pathlib import Path
from collections import Counter
from itertools import combinations
from datetime import datetime

import numpy as np
import pandas as pd

from src.lottery.config.lottery_game_rules import (
    get_current_rule,
    get_prediction_regular_range,
    get_prediction_bonus_range,
    get_max_historical_regular_number,
    get_max_historical_bonus_number,
    get_dynamic_buckets,
    get_upper_start,
    get_upper_elite,
)


BASE_DIR = Path(__file__).resolve().parents[3]
FEATURES_FILE = BASE_DIR / "data" / "processed" / "features" / "lotto_features.xlsx"
EXPORT_DIR = BASE_DIR / "data" / "exports" / "predictions"
OUTPUT_FILE = EXPORT_DIR / "lotto_predictions.xlsx"

GAME_NAME = "Lotto"
CURRENT_RULE = get_current_rule(GAME_NAME)

PREDICTION_REGULAR_RANGE = get_prediction_regular_range(GAME_NAME)
PREDICTION_BONUS_RANGE = get_prediction_bonus_range(GAME_NAME)

HISTORICAL_REGULAR_RANGE = range(1, get_max_historical_regular_number(GAME_NAME) + 1)
_historical_bonus_max = get_max_historical_bonus_number(GAME_NAME)
HISTORICAL_BONUS_RANGE = range(1, _historical_bonus_max + 1) if _historical_bonus_max else None

REGULAR_PICK_COUNT = CURRENT_RULE.regular_pick_count
HAS_BONUS = PREDICTION_BONUS_RANGE is not None and CURRENT_RULE.bonus_pick_count > 0

LOW_HIGH_MIDPOINT = CURRENT_RULE.regular_max // 2
RANGE_BUCKETS = get_dynamic_buckets(CURRENT_RULE)
UPPER_START = get_upper_start(CURRENT_RULE)
UPPER_ELITE = get_upper_elite(CURRENT_RULE)

SIMULATION_COUNT = 7000
TOP_PREDICTIONS = 10
RNG_SEED = 42
_rng = np.random.default_rng(RNG_SEED)

MAX_OVERLAP_BETWEEN_OUTPUTS = 4
MAX_OVERLAP_WITH_HISTORY = 5
RECENCY_DECAY = 0.985

WEIGHT_FREQUENCY = 1.4
WEIGHT_RECENCY = 1.8
WEIGHT_OVERDUE = 1.8
WEIGHT_PAIR = 0.55
WEIGHT_PATTERN = 0.80
WEIGHT_BUCKET_BALANCE = 1.25
WEIGHT_UPPER_RANGE = 1.75

MIN_REGULAR_SUM = int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT * 0.30)
MAX_REGULAR_SUM = int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT * 0.88)

REGULAR_COLS = [f"N{i}" for i in range(1, REGULAR_PICK_COUNT + 1)]
BONUS_COL = "Bonus"


def load_lotto_features() -> pd.DataFrame:
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
        df = df[df["GameName"].astype(str).str.strip().str.lower() == GAME_NAME.lower()].copy()

    return df.sort_values(by=["DrawDate"], ascending=False).reset_index(drop=True)


def normalise_01(series) -> pd.Series:
    series = pd.Series(series, dtype=float)
    lo = series.min()
    hi = series.max()
    if hi <= lo:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)


def get_regular_numbers(row) -> list[int]:
    return [int(row[col]) for col in REGULAR_COLS if col in row and pd.notna(row[col])]


def get_bonus_number(row) -> int | None:
    if BONUS_COL not in row or pd.isna(row[BONUS_COL]):
        return None
    return int(row[BONUS_COL])


def weighted_choice_no_replace(candidates, weights, k):
    candidates = np.array(list(candidates), dtype=int)
    weights = np.array(list(weights), dtype=float)
    if len(candidates) == 0:
        return []
    probs = np.ones(len(candidates)) / len(candidates) if weights.sum() <= 0 else weights / weights.sum()
    return _rng.choice(candidates, size=min(k, len(candidates)), replace=False, p=probs).tolist()


def count_high_low(numbers):
    low_count = sum(1 for n in numbers if n <= LOW_HIGH_MIDPOINT)
    high_count = len(numbers) - low_count
    return high_count, low_count


def count_odd_even(numbers):
    odd_count = sum(1 for n in numbers if n % 2 != 0)
    return odd_count, len(numbers) - odd_count


def count_bucket_numbers(numbers):
    bucket_counts = {}
    for bucket_name, bucket_range in RANGE_BUCKETS.items():
        bucket_set = set(bucket_range)
        bucket_counts[bucket_name] = sum(1 for n in numbers if n in bucket_set)
    return bucket_counts


def bucket_balance_score(numbers):
    bucket_counts = count_bucket_numbers(numbers)
    occupied_buckets = sum(1 for count in bucket_counts.values() if count > 0)
    max_bucket_count = max(bucket_counts.values())
    score = occupied_buckets * 4
    if max_bucket_count <= 3:
        score += 6
    if bucket_counts["HIGH"] >= 1:
        score += 10
    if bucket_counts["HIGH"] >= 2:
        score += 8
    if bucket_counts["LOW"] >= 1 and bucket_counts["HIGH"] >= 1:
        score += 5
    return score


def upper_range_score(numbers):
    count_upper = sum(1 for n in numbers if n >= UPPER_START)
    count_elite = sum(1 for n in numbers if n >= UPPER_ELITE)
    score = 0
    if count_upper >= 1:
        score += 10
    if count_upper >= 2:
        score += 8
    if count_elite >= 1:
        score += 6
    return score


def consecutive_pairs(numbers):
    numbers = sorted(numbers)
    return sum(1 for i in range(len(numbers) - 1) if numbers[i + 1] - numbers[i] == 1)


def has_too_much_history_overlap(numbers, history_sets):
    number_set = set(numbers)
    return any(len(number_set.intersection(hist_set)) > MAX_OVERLAP_WITH_HISTORY for hist_set in history_sets)


def output_diversity_ok(candidate, selected):
    candidate_set = set(candidate[:REGULAR_PICK_COUNT])
    for existing in selected:
        existing_set = set(existing[:REGULAR_PICK_COUNT])
        if len(candidate_set.intersection(existing_set)) > MAX_OVERLAP_BETWEEN_OUTPUTS:
            return False
    return True


def build_frequency_scores(df):
    regular_counter = Counter()
    bonus_counter = Counter()

    for _, row in df.iterrows():
        for n in get_regular_numbers(row):
            if n in HISTORICAL_REGULAR_RANGE:
                regular_counter[n] += 1

        bonus = get_bonus_number(row)
        if bonus is not None and HISTORICAL_BONUS_RANGE is not None and bonus in HISTORICAL_BONUS_RANGE:
            bonus_counter[bonus] += 1

    regular_scores = pd.Series({n: regular_counter[n] for n in HISTORICAL_REGULAR_RANGE})
    bonus_scores = (
        pd.Series({n: bonus_counter[n] for n in HISTORICAL_BONUS_RANGE})
        if HISTORICAL_BONUS_RANGE is not None else pd.Series(dtype=float)
    )
    return normalise_01(regular_scores), normalise_01(bonus_scores)


def build_recency_scores(df):
    regular_scores = pd.Series(0.0, index=pd.Index(HISTORICAL_REGULAR_RANGE), dtype=float)
    bonus_scores = (
        pd.Series(0.0, index=pd.Index(HISTORICAL_BONUS_RANGE), dtype=float)
        if HISTORICAL_BONUS_RANGE is not None else pd.Series(dtype=float)
    )

    for idx, row in df.iterrows():
        weight = RECENCY_DECAY ** idx
        for n in get_regular_numbers(row):
            if n in regular_scores.index:
                regular_scores.loc[n] += weight

        bonus = get_bonus_number(row)
        if bonus is not None and not bonus_scores.empty and bonus in bonus_scores.index:
            bonus_scores.loc[bonus] += weight

    return normalise_01(regular_scores), normalise_01(bonus_scores)


def build_overdue_scores(df):
    last_seen = {n: None for n in HISTORICAL_REGULAR_RANGE}

    for idx, row in df.iterrows():
        for n in get_regular_numbers(row):
            if n in last_seen and last_seen[n] is None:
                last_seen[n] = idx

    overdue = {n: (len(df) * 1.25 if last_seen[n] is None else last_seen[n]) for n in HISTORICAL_REGULAR_RANGE}
    return normalise_01(pd.Series(overdue))


def build_pair_scores(df):
    pair_counter = Counter()
    for _, row in df.iterrows():
        numbers = sorted(n for n in get_regular_numbers(row) if n in HISTORICAL_REGULAR_RANGE)
        for pair in combinations(numbers, 2):
            pair_counter[pair] += 1
    return pair_counter


def build_pattern_distributions(df):
    high_low_counter = Counter()
    odd_even_counter = Counter()
    sum_band_counter = Counter()
    bucket_counter = Counter()

    for _, row in df.iterrows():
        numbers = [n for n in get_regular_numbers(row) if n in PREDICTION_REGULAR_RANGE]
        if len(numbers) != REGULAR_PICK_COUNT:
            continue

        high_low_counter[count_high_low(numbers)] += 1
        odd_even_counter[count_odd_even(numbers)] += 1

        regular_sum = sum(numbers)
        if regular_sum <= CURRENT_RULE.regular_max * 2.5:
            sum_band = "Low Sum"
        elif regular_sum <= CURRENT_RULE.regular_max * 3.5:
            sum_band = "Mid Sum"
        elif regular_sum <= CURRENT_RULE.regular_max * 4.5:
            sum_band = "High Sum"
        else:
            sum_band = "Extreme Sum"

        sum_band_counter[sum_band] += 1
        bucket_counter[tuple(count_bucket_numbers(numbers).values())] += 1

    return {
        "high_low": high_low_counter,
        "odd_even": odd_even_counter,
        "sum_band": sum_band_counter,
        "bucket": bucket_counter,
    }


def build_number_weights(df):
    freq_reg, freq_bonus = build_frequency_scores(df)
    rec_reg, rec_bonus = build_recency_scores(df)
    overdue_reg = build_overdue_scores(df)

    regular_weights_all = (WEIGHT_FREQUENCY * freq_reg + WEIGHT_RECENCY * rec_reg + WEIGHT_OVERDUE * overdue_reg)

    # Only expose legal current prediction numbers.
    regular_weights = regular_weights_all.reindex(list(PREDICTION_REGULAR_RANGE)).fillna(0.001)

    for n in PREDICTION_REGULAR_RANGE:
        if n >= UPPER_START:
            regular_weights.loc[n] *= 1.35
        if n >= UPPER_ELITE:
            regular_weights.loc[n] *= 1.20

    regular_weights = regular_weights.clip(lower=0.001)

    if HAS_BONUS:
        bonus_weights_all = (WEIGHT_FREQUENCY * freq_bonus + WEIGHT_RECENCY * rec_bonus)
        bonus_weights = bonus_weights_all.reindex(list(PREDICTION_BONUS_RANGE)).fillna(0.001).clip(lower=0.001)
    else:
        bonus_weights = pd.Series(dtype=float)

    return regular_weights.to_dict(), bonus_weights.to_dict()


def score_pair_strength(numbers, pair_counter):
    return sum(pair_counter[pair] for pair in combinations(sorted(numbers), 2))


def score_pattern_fit(numbers, pattern_distributions):
    high_low = count_high_low(numbers)
    odd_even = count_odd_even(numbers)
    regular_sum = sum(numbers)

    if regular_sum <= CURRENT_RULE.regular_max * 2.5:
        sum_band = "Low Sum"
    elif regular_sum <= CURRENT_RULE.regular_max * 3.5:
        sum_band = "Mid Sum"
    elif regular_sum <= CURRENT_RULE.regular_max * 4.5:
        sum_band = "High Sum"
    else:
        sum_band = "Extreme Sum"

    bucket_signature = tuple(count_bucket_numbers(numbers).values())
    return (
        pattern_distributions["high_low"][high_low]
        + pattern_distributions["odd_even"][odd_even]
        + pattern_distributions["sum_band"][sum_band]
        + pattern_distributions["bucket"][bucket_signature]
    )


def calculate_confidence(raw_score, max_score):
    if max_score <= 0:
        return 50.0
    return round(min(60 + ((raw_score / max_score) * 35), 95), 2)


def generate_candidate(regular_weights, bonus_weights):
    regular_numbers = weighted_choice_no_replace(
        candidates=list(PREDICTION_REGULAR_RANGE),
        weights=[regular_weights[n] for n in PREDICTION_REGULAR_RANGE],
        k=REGULAR_PICK_COUNT,
    )
    regular_numbers = sorted(regular_numbers)

    if HAS_BONUS:
        bonus_pool = [n for n in PREDICTION_BONUS_RANGE if n not in regular_numbers]
        bonus = weighted_choice_no_replace(
            candidates=bonus_pool,
            weights=[bonus_weights[n] for n in bonus_pool],
            k=1,
        )[0]
    else:
        bonus = None

    return regular_numbers, bonus


def generate_predictions(simulation_count=SIMULATION_COUNT, top_n=TOP_PREDICTIONS):
    df = load_lotto_features()
    regular_weights, bonus_weights = build_number_weights(df)
    pair_counter = build_pair_scores(df)
    pattern_distributions = build_pattern_distributions(df)
    history_sets = [set(get_regular_numbers(row)) for _, row in df.iterrows()]

    candidates = []
    attempts = 0
    max_attempts = simulation_count * 30

    while len(candidates) < simulation_count and attempts < max_attempts:
        attempts += 1
        numbers, bonus = generate_candidate(regular_weights, bonus_weights)

        if has_too_much_history_overlap(numbers, history_sets):
            continue
        if consecutive_pairs(numbers) > 3:
            continue

        high_count, low_count = count_high_low(numbers)
        odd_count, even_count = count_odd_even(numbers)
        regular_sum = sum(numbers)

        if regular_sum < MIN_REGULAR_SUM or regular_sum > MAX_REGULAR_SUM:
            continue

        bucket_counts = count_bucket_numbers(numbers)
        if bucket_counts["HIGH"] == 0:
            continue

        base_score = sum(regular_weights[n] for n in numbers)
        if HAS_BONUS and bonus is not None:
            base_score += bonus_weights[bonus]

        raw_score = (
            base_score
            + (WEIGHT_PAIR * score_pair_strength(numbers, pair_counter))
            + (WEIGHT_PATTERN * score_pattern_fit(numbers, pattern_distributions))
            + (WEIGHT_BUCKET_BALANCE * bucket_balance_score(numbers))
            + (WEIGHT_UPPER_RANGE * upper_range_score(numbers))
        )

        row = {
            **{f"N{i + 1}": numbers[i] for i in range(REGULAR_PICK_COUNT)},
            "RegularSum": regular_sum,
            "HighCount": high_count,
            "LowCount": low_count,
            "OddCount": odd_count,
            "EvenCount": even_count,
            "Bucket_LOW": bucket_counts["LOW"],
            "Bucket_MID_LOW": bucket_counts["MID_LOW"],
            "Bucket_MID_HIGH": bucket_counts["MID_HIGH"],
            "Bucket_HIGH": bucket_counts["HIGH"],
            "UpperRangeCount": sum(1 for n in numbers if n >= UPPER_START),
            "ConsecutivePairs": consecutive_pairs(numbers),
            "RawScore": raw_score,
        }
        if HAS_BONUS:
            row["Bonus"] = bonus
        candidates.append(row)

    if not candidates:
        raise ValueError("No candidates generated. Relax the model filters.")

    subset_cols = REGULAR_COLS + (["Bonus"] if HAS_BONUS else [])
    candidate_df = pd.DataFrame(candidates).drop_duplicates(subset=subset_cols)
    candidate_df = candidate_df.sort_values(by="RawScore", ascending=False).reset_index(drop=True)
    max_score = candidate_df["RawScore"].max()
    candidate_df["Confidence"] = candidate_df["RawScore"].apply(lambda x: calculate_confidence(x, max_score))

    selected_rows = []
    for _, row in candidate_df.iterrows():
        candidate = [int(row[col]) for col in REGULAR_COLS]
        if HAS_BONUS:
            candidate.append(int(row["Bonus"]))
        if output_diversity_ok(candidate, selected_rows):
            selected_rows.append(candidate)
        if len(selected_rows) >= top_n:
            break

    final_rows = []
    for rank, candidate in enumerate(selected_rows, start=1):
        mask = True
        for i, col in enumerate(REGULAR_COLS):
            mask = mask & (candidate_df[col] == candidate[i])
        if HAS_BONUS:
            mask = mask & (candidate_df["Bonus"] == candidate[-1])
        match = candidate_df[mask].iloc[0]

        output = {
            "PredictionRank": rank,
            **{col: int(match[col]) for col in REGULAR_COLS},
            "RegularSum": int(match["RegularSum"]),
            "HighCount": int(match["HighCount"]),
            "LowCount": int(match["LowCount"]),
            "OddCount": int(match["OddCount"]),
            "EvenCount": int(match["EvenCount"]),
            "Bucket_LOW": int(match["Bucket_LOW"]),
            "Bucket_MID_LOW": int(match["Bucket_MID_LOW"]),
            "Bucket_MID_HIGH": int(match["Bucket_MID_HIGH"]),
            "Bucket_HIGH": int(match["Bucket_HIGH"]),
            "UpperRangeCount": int(match["UpperRangeCount"]),
            "ConsecutivePairs": int(match["ConsecutivePairs"]),
            "RawScore": round(float(match["RawScore"]), 4),
            "Confidence": float(match["Confidence"]),
            "RuleVersion": CURRENT_RULE.rule_version,
            "ModelVersion": "Lotto_v3_rules_aware",
            "GeneratedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if HAS_BONUS:
            output["Bonus"] = int(match["Bonus"])
        final_rows.append(output)

    return pd.DataFrame(final_rows)


def export_lotto_predictions(simulation_count=SIMULATION_COUNT, top_n=TOP_PREDICTIONS):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    predictions = generate_predictions(simulation_count=simulation_count, top_n=top_n)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl", mode="w") as writer:
        predictions.to_excel(writer, sheet_name="Lotto_Predictions", index=False)

    print("\nLotto predictions exported.")
    print(f"Rows: {len(predictions)}")
    print(f"Rule: {CURRENT_RULE.rule_version} | Range: {CURRENT_RULE.regular_min}-{CURRENT_RULE.regular_max}")
    print(f"File: {OUTPUT_FILE}")
    return predictions


def main():
    export_lotto_predictions()


if __name__ == "__main__":
    main()
