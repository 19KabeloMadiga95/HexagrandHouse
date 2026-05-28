from pathlib import Path
from collections import Counter
from itertools import combinations
from datetime import datetime

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]

FEATURES_FILE = BASE_DIR / "data" / "processed" / "features" / "lotto_features.xlsx"

EXPORT_DIR = BASE_DIR / "data" / "exports" / "predictions"
OUTPUT_FILE = EXPORT_DIR / "lotto_predictions.xlsx"


REGULAR_RANGE = range(1, 59)
BONUS_RANGE = range(1, 59)

POST_EXPANSION_DATE = pd.Timestamp("2025-09-01")

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

RANGE_BUCKETS = {
    "LOW": range(1, 15),
    "MID_LOW": range(15, 30),
    "MID_HIGH": range(30, 45),
    "HIGH": range(45, 59),
}


def load_lotto_features():
    if not FEATURES_FILE.exists():
        raise FileNotFoundError(
            f"Lotto features file not found:\n{FEATURES_FILE}\n\n"
            "Run this first:\n"
            "python -m src.lottery.features.lotto_features"
        )

    df = pd.read_excel(
        FEATURES_FILE,
        sheet_name="Lotto_Features",
        engine="openpyxl"
    )

    df["DrawDate"] = pd.to_datetime(df["DrawDate"], errors="coerce")

    number_cols = ["N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]

    for col in number_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=["DrawDate", "N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]
    )

    df = df.sort_values(
        by=["DrawDate", "GameName"],
        ascending=[False, True]
    ).reset_index(drop=True)

    return df


def normalise_01(series):
    series = pd.Series(series, dtype=float)

    lo = series.min()
    hi = series.max()

    if hi <= lo:
        return pd.Series(0.5, index=series.index)

    return (series - lo) / (hi - lo)


def get_regular_numbers(row):
    return [
        int(row["N1"]),
        int(row["N2"]),
        int(row["N3"]),
        int(row["N4"]),
        int(row["N5"]),
        int(row["N6"]),
    ]


def weighted_choice_no_replace(candidates, weights, k):
    candidates = np.array(candidates, dtype=int)
    weights = np.array(weights, dtype=float)

    if len(candidates) == 0:
        return []

    if weights.sum() <= 0:
        probs = np.ones(len(candidates)) / len(candidates)
    else:
        probs = weights / weights.sum()

    k = min(k, len(candidates))

    return _rng.choice(
        candidates,
        size=k,
        replace=False,
        p=probs
    ).tolist()


def count_high_low(numbers):
    low_count = sum(1 for n in numbers if n <= 29)
    high_count = len(numbers) - low_count

    return high_count, low_count


def count_odd_even(numbers):
    odd_count = sum(1 for n in numbers if n % 2 != 0)
    even_count = len(numbers) - odd_count

    return odd_count, even_count


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

    score = 0

    score += occupied_buckets * 4

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
    count_50_plus = sum(1 for n in numbers if n >= 50)
    count_53_plus = sum(1 for n in numbers if n >= 53)

    score = 0

    if count_50_plus >= 1:
        score += 10

    if count_50_plus >= 2:
        score += 8

    if count_53_plus >= 1:
        score += 6

    return score


def consecutive_pairs(numbers):
    numbers = sorted(numbers)
    count = 0

    for i in range(len(numbers) - 1):
        if numbers[i + 1] - numbers[i] == 1:
            count += 1

    return count


def has_too_much_history_overlap(numbers, history_sets):
    number_set = set(numbers)

    for hist_set in history_sets:
        overlap = len(number_set.intersection(hist_set))

        if overlap > MAX_OVERLAP_WITH_HISTORY:
            return True

    return False


def output_diversity_ok(candidate, selected):
    candidate_set = set(candidate[:6])

    for existing in selected:
        existing_set = set(existing[:6])
        overlap = len(candidate_set.intersection(existing_set))

        if overlap > MAX_OVERLAP_BETWEEN_OUTPUTS:
            return False

    return True


def era_weight(draw_date):
    if pd.isna(draw_date):
        return 0.50

    if draw_date >= POST_EXPANSION_DATE:
        return 3.0

    return 0.45


def build_frequency_scores(df):
    regular_counter = Counter()
    bonus_counter = Counter()

    for _, row in df.iterrows():
        weight = era_weight(row["DrawDate"])

        for n in get_regular_numbers(row):
            regular_counter[n] += weight

        bonus_counter[int(row["Bonus"])] += weight

    regular_scores = pd.Series(
        {n: regular_counter[n] for n in REGULAR_RANGE}
    )

    bonus_scores = pd.Series(
        {n: bonus_counter[n] for n in BONUS_RANGE}
    )

    return normalise_01(regular_scores), normalise_01(bonus_scores)


def build_recency_scores(df):
    regular_scores = pd.Series(
        0.0,
        index=pd.Index(REGULAR_RANGE),
        dtype=float
    )

    bonus_scores = pd.Series(
        0.0,
        index=pd.Index(BONUS_RANGE),
        dtype=float
    )

    for idx, row in df.iterrows():
        weight = (RECENCY_DECAY ** idx) * era_weight(row["DrawDate"])

        for n in get_regular_numbers(row):
            regular_scores.loc[n] += weight

        bonus_scores.loc[int(row["Bonus"])] += weight

    return normalise_01(regular_scores), normalise_01(bonus_scores)


def build_overdue_scores(df):
    last_seen = {n: None for n in REGULAR_RANGE}

    for idx, row in df.iterrows():
        for n in get_regular_numbers(row):
            if last_seen[n] is None:
                last_seen[n] = idx

    overdue = {}

    for n in REGULAR_RANGE:
        if last_seen[n] is None:
            overdue[n] = len(df) * 1.25
        else:
            overdue[n] = last_seen[n]

    return normalise_01(pd.Series(overdue))


def build_pair_scores(df):
    pair_counter = Counter()

    for _, row in df.iterrows():
        weight = era_weight(row["DrawDate"])
        numbers = sorted(get_regular_numbers(row))

        for pair in combinations(numbers, 2):
            pair_counter[pair] += weight

    return pair_counter


def build_pattern_distributions(df):
    high_low_counter = Counter()
    odd_even_counter = Counter()
    sum_band_counter = Counter()
    bucket_counter = Counter()

    for _, row in df.iterrows():
        weight = era_weight(row["DrawDate"])
        numbers = get_regular_numbers(row)

        high_low_counter[count_high_low(numbers)] += weight
        odd_even_counter[count_odd_even(numbers)] += weight

        regular_sum = sum(numbers)

        if regular_sum <= 140:
            sum_band = "Low Sum"
        elif regular_sum <= 190:
            sum_band = "Mid Sum"
        elif regular_sum <= 250:
            sum_band = "High Sum"
        else:
            sum_band = "Extreme Sum"

        sum_band_counter[sum_band] += weight

        bucket_counts = count_bucket_numbers(numbers)
        bucket_signature = tuple(bucket_counts.values())
        bucket_counter[bucket_signature] += weight

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

    regular_weights = (
        WEIGHT_FREQUENCY * freq_reg
        + WEIGHT_RECENCY * rec_reg
        + WEIGHT_OVERDUE * overdue_reg
    )

    bonus_weights = (
        WEIGHT_FREQUENCY * freq_bonus
        + WEIGHT_RECENCY * rec_bonus
    )

    for n in REGULAR_RANGE:
        if n >= 50:
            regular_weights.loc[n] *= 1.35

        if n >= 53:
            regular_weights.loc[n] *= 1.20

    for n in BONUS_RANGE:
        if n >= 50:
            bonus_weights.loc[n] *= 1.25

    regular_weights = regular_weights.clip(lower=0.001)
    bonus_weights = bonus_weights.clip(lower=0.001)

    return regular_weights.to_dict(), bonus_weights.to_dict()


def score_pair_strength(numbers, pair_counter):
    score = 0

    for pair in combinations(sorted(numbers), 2):
        score += pair_counter[pair]

    return score


def score_pattern_fit(numbers, pattern_distributions):
    high_low = count_high_low(numbers)
    odd_even = count_odd_even(numbers)
    regular_sum = sum(numbers)

    if regular_sum <= 140:
        sum_band = "Low Sum"
    elif regular_sum <= 190:
        sum_band = "Mid Sum"
    elif regular_sum <= 250:
        sum_band = "High Sum"
    else:
        sum_band = "Extreme Sum"

    bucket_counts = count_bucket_numbers(numbers)
    bucket_signature = tuple(bucket_counts.values())

    high_low_score = pattern_distributions["high_low"][high_low]
    odd_even_score = pattern_distributions["odd_even"][odd_even]
    sum_band_score = pattern_distributions["sum_band"][sum_band]
    bucket_score = pattern_distributions["bucket"][bucket_signature]

    return high_low_score + odd_even_score + sum_band_score + bucket_score


def calculate_confidence(raw_score, max_score):
    if max_score <= 0:
        return 50.0

    confidence = 60 + ((raw_score / max_score) * 35)

    return round(min(confidence, 95), 2)


def generate_candidate(regular_weights, bonus_weights):
    regular_numbers = weighted_choice_no_replace(
        candidates=list(REGULAR_RANGE),
        weights=[regular_weights[n] for n in REGULAR_RANGE],
        k=6
    )

    regular_numbers = sorted(regular_numbers)

    bonus_pool = [
        n for n in BONUS_RANGE
        if n not in regular_numbers
    ]

    bonus = weighted_choice_no_replace(
        candidates=bonus_pool,
        weights=[bonus_weights[n] for n in bonus_pool],
        k=1
    )[0]

    return regular_numbers, bonus


def generate_predictions(
    simulation_count=SIMULATION_COUNT,
    top_n=TOP_PREDICTIONS,
):
    df = load_lotto_features()

    regular_weights, bonus_weights = build_number_weights(df)
    pair_counter = build_pair_scores(df)
    pattern_distributions = build_pattern_distributions(df)

    history_sets = [
        set(get_regular_numbers(row))
        for _, row in df.iterrows()
    ]

    candidates = []

    attempts = 0
    max_attempts = simulation_count * 30

    while len(candidates) < simulation_count and attempts < max_attempts:
        attempts += 1

        numbers, bonus = generate_candidate(
            regular_weights,
            bonus_weights
        )

        if has_too_much_history_overlap(numbers, history_sets):
            continue

        if consecutive_pairs(numbers) > 3:
            continue

        high_count, low_count = count_high_low(numbers)
        odd_count, even_count = count_odd_even(numbers)

        regular_sum = sum(numbers)

        if regular_sum < 95 or regular_sum > 285:
            continue

        bucket_counts = count_bucket_numbers(numbers)

        if bucket_counts["HIGH"] == 0:
            continue

        base_score = (
            sum(regular_weights[n] for n in numbers)
            + bonus_weights[bonus]
        )

        pair_score = score_pair_strength(numbers, pair_counter)
        pattern_score = score_pattern_fit(numbers, pattern_distributions)
        bucket_score = bucket_balance_score(numbers)
        upper_score = upper_range_score(numbers)

        raw_score = (
            base_score
            + (WEIGHT_PAIR * pair_score)
            + (WEIGHT_PATTERN * pattern_score)
            + (WEIGHT_BUCKET_BALANCE * bucket_score)
            + (WEIGHT_UPPER_RANGE * upper_score)
        )

        candidates.append({
            "N1": numbers[0],
            "N2": numbers[1],
            "N3": numbers[2],
            "N4": numbers[3],
            "N5": numbers[4],
            "N6": numbers[5],
            "Bonus": bonus,
            "RegularSum": regular_sum,
            "HighCount": high_count,
            "LowCount": low_count,
            "OddCount": odd_count,
            "EvenCount": even_count,
            "Bucket_LOW": bucket_counts["LOW"],
            "Bucket_MID_LOW": bucket_counts["MID_LOW"],
            "Bucket_MID_HIGH": bucket_counts["MID_HIGH"],
            "Bucket_HIGH": bucket_counts["HIGH"],
            "Upper50PlusCount": sum(1 for n in numbers if n >= 50),
            "ConsecutivePairs": consecutive_pairs(numbers),
            "RawScore": raw_score,
        })

    if not candidates:
        raise ValueError("No candidates generated. Relax the model filters.")

    candidate_df = pd.DataFrame(candidates)

    candidate_df = candidate_df.drop_duplicates(
        subset=["N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]
    )

    candidate_df = candidate_df.sort_values(
        by=["RawScore"],
        ascending=False
    ).reset_index(drop=True)

    max_score = candidate_df["RawScore"].max()

    candidate_df["Confidence"] = candidate_df["RawScore"].apply(
        lambda x: calculate_confidence(x, max_score)
    )

    selected_rows = []

    for _, row in candidate_df.iterrows():
        candidate = [
            int(row["N1"]),
            int(row["N2"]),
            int(row["N3"]),
            int(row["N4"]),
            int(row["N5"]),
            int(row["N6"]),
            int(row["Bonus"]),
        ]

        if output_diversity_ok(candidate, selected_rows):
            selected_rows.append(candidate)

        if len(selected_rows) >= top_n:
            break

    final_rows = []

    for rank, candidate in enumerate(selected_rows, start=1):
        match = candidate_df[
            (candidate_df["N1"] == candidate[0])
            & (candidate_df["N2"] == candidate[1])
            & (candidate_df["N3"] == candidate[2])
            & (candidate_df["N4"] == candidate[3])
            & (candidate_df["N5"] == candidate[4])
            & (candidate_df["N6"] == candidate[5])
            & (candidate_df["Bonus"] == candidate[6])
        ].iloc[0]

        final_rows.append({
            "PredictionRank": rank,
            "N1": candidate[0],
            "N2": candidate[1],
            "N3": candidate[2],
            "N4": candidate[3],
            "N5": candidate[4],
            "N6": candidate[5],
            "Bonus": candidate[6],
            "RegularSum": int(match["RegularSum"]),
            "HighCount": int(match["HighCount"]),
            "LowCount": int(match["LowCount"]),
            "OddCount": int(match["OddCount"]),
            "EvenCount": int(match["EvenCount"]),
            "Bucket_LOW": int(match["Bucket_LOW"]),
            "Bucket_MID_LOW": int(match["Bucket_MID_LOW"]),
            "Bucket_MID_HIGH": int(match["Bucket_MID_HIGH"]),
            "Bucket_HIGH": int(match["Bucket_HIGH"]),
            "Upper50PlusCount": int(match["Upper50PlusCount"]),
            "ConsecutivePairs": int(match["ConsecutivePairs"]),
            "RawScore": round(float(match["RawScore"]), 4),
            "Confidence": float(match["Confidence"]),
            "ModelVersion": "Lotto_v2_range_balanced",
            "GeneratedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    return pd.DataFrame(final_rows)


def export_lotto_predictions(
    simulation_count=SIMULATION_COUNT,
    top_n=TOP_PREDICTIONS,
):
    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    predictions = generate_predictions(
        simulation_count=simulation_count,
        top_n=top_n
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:
        predictions.to_excel(
            writer,
            sheet_name="Lotto_Predictions",
            index=False
        )

    print("\nLotto predictions exported.")
    print(f"Rows: {len(predictions)}")
    print(f"File: {OUTPUT_FILE}")

    return predictions


def main():
    export_lotto_predictions()


if __name__ == "__main__":
    main()