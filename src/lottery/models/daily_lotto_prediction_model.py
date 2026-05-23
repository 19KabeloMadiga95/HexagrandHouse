from pathlib import Path
from collections import Counter
from itertools import combinations
from datetime import datetime

import numpy as np
import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

FEATURES_FILE = BASE_DIR / "data" / "processed" / "features" / "daily_lotto_features.xlsx"

EXPORT_DIR = BASE_DIR / "data" / "exports" / "predictions"
OUTPUT_FILE = EXPORT_DIR / "daily_lotto_predictions.xlsx"


# =========================================================
# MODEL CONFIG
# =========================================================

REGULAR_RANGE = range(1, 37)

LOW_REGULAR_MAX = 18

SIMULATION_COUNT = 5000
TOP_PREDICTIONS = 10

RNG_SEED = 42
_rng = np.random.default_rng(RNG_SEED)

MAX_OVERLAP_BETWEEN_OUTPUTS = 3
MAX_OVERLAP_WITH_HISTORY = 4

RECENCY_DECAY = 0.975

WEIGHT_FREQUENCY = 2.2
WEIGHT_RECENCY = 2.0
WEIGHT_OVERDUE = 1.0
WEIGHT_PAIR = 0.9
WEIGHT_PATTERN = 1.0


# =========================================================
# LOAD DATA
# =========================================================

def load_daily_lotto_features():
    if not FEATURES_FILE.exists():
        raise FileNotFoundError(
            f"Daily Lotto features file not found:\n{FEATURES_FILE}\n\n"
            "Run this first:\n"
            "python -m src.lottery.features.daily_lotto_features"
        )

    df = pd.read_excel(
        FEATURES_FILE,
        sheet_name="Daily_Lotto_Features",
        engine="openpyxl"
    )

    df["DrawDate"] = pd.to_datetime(df["DrawDate"], errors="coerce")

    number_cols = ["N1", "N2", "N3", "N4", "N5"]

    for col in number_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=["DrawDate", "N1", "N2", "N3", "N4", "N5"]
    )

    df = df.sort_values(
        by=["DrawDate"],
        ascending=False
    ).reset_index(drop=True)

    return df


# =========================================================
# HELPERS
# =========================================================

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
    low_count = sum(1 for n in numbers if n <= LOW_REGULAR_MAX)
    high_count = len(numbers) - low_count

    return high_count, low_count


def count_odd_even(numbers):
    odd_count = sum(1 for n in numbers if n % 2 != 0)
    even_count = len(numbers) - odd_count

    return odd_count, even_count


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
    candidate_set = set(candidate[:5])

    for existing in selected:
        existing_set = set(existing[:5])
        overlap = len(candidate_set.intersection(existing_set))

        if overlap > MAX_OVERLAP_BETWEEN_OUTPUTS:
            return False

    return True


# =========================================================
# MODEL LEARNING
# =========================================================

def build_frequency_scores(df):
    regular_counter = Counter()

    for _, row in df.iterrows():
        for n in get_regular_numbers(row):
            regular_counter[n] += 1

    regular_scores = pd.Series(
        {n: regular_counter[n] for n in REGULAR_RANGE}
    )

    return normalise_01(regular_scores)


def build_recency_scores(df):
    regular_scores = pd.Series(
        0.0,
        index=pd.Index(REGULAR_RANGE),
        dtype=float
    )

    for idx, row in df.iterrows():
        weight = RECENCY_DECAY ** idx

        for n in get_regular_numbers(row):
            regular_scores.loc[n] += weight

    return normalise_01(regular_scores)


def build_overdue_scores(df):
    last_seen = {n: None for n in REGULAR_RANGE}

    for idx, row in df.iterrows():
        for n in get_regular_numbers(row):
            if last_seen[n] is None:
                last_seen[n] = idx

    overdue = {}

    for n in REGULAR_RANGE:
        if last_seen[n] is None:
            overdue[n] = len(df)
        else:
            overdue[n] = last_seen[n]

    return normalise_01(pd.Series(overdue))


def build_pair_scores(df):
    pair_counter = Counter()

    for _, row in df.iterrows():
        numbers = sorted(get_regular_numbers(row))

        for pair in combinations(numbers, 2):
            pair_counter[pair] += 1

    return pair_counter


def build_pattern_distributions(df):
    high_low_counter = Counter()
    odd_even_counter = Counter()
    sum_band_counter = Counter()

    for _, row in df.iterrows():
        numbers = get_regular_numbers(row)

        high_low_counter[count_high_low(numbers)] += 1
        odd_even_counter[count_odd_even(numbers)] += 1

        regular_sum = sum(numbers)

        if regular_sum <= 60:
            sum_band = "Low Sum"
        elif regular_sum <= 95:
            sum_band = "Mid Sum"
        elif regular_sum <= 130:
            sum_band = "High Sum"
        else:
            sum_band = "Extreme Sum"

        sum_band_counter[sum_band] += 1

    return {
        "high_low": high_low_counter,
        "odd_even": odd_even_counter,
        "sum_band": sum_band_counter,
    }


def build_number_weights(df):
    freq_reg = build_frequency_scores(df)
    rec_reg = build_recency_scores(df)
    overdue_reg = build_overdue_scores(df)

    regular_weights = (
        WEIGHT_FREQUENCY * freq_reg
        + WEIGHT_RECENCY * rec_reg
        + WEIGHT_OVERDUE * overdue_reg
    )

    regular_weights = regular_weights.clip(lower=0.001)

    return regular_weights.to_dict()


# =========================================================
# CANDIDATE SCORING
# =========================================================

def score_pair_strength(numbers, pair_counter):
    score = 0

    for pair in combinations(sorted(numbers), 2):
        score += pair_counter[pair]

    return score


def score_pattern_fit(numbers, pattern_distributions):
    high_low = count_high_low(numbers)
    odd_even = count_odd_even(numbers)
    regular_sum = sum(numbers)

    if regular_sum <= 60:
        sum_band = "Low Sum"
    elif regular_sum <= 95:
        sum_band = "Mid Sum"
    elif regular_sum <= 130:
        sum_band = "High Sum"
    else:
        sum_band = "Extreme Sum"

    high_low_score = pattern_distributions["high_low"][high_low]
    odd_even_score = pattern_distributions["odd_even"][odd_even]
    sum_band_score = pattern_distributions["sum_band"][sum_band]

    return high_low_score + odd_even_score + sum_band_score


def calculate_confidence(raw_score, max_score):
    if max_score <= 0:
        return 50.0

    confidence = 60 + ((raw_score / max_score) * 35)

    return round(min(confidence, 95), 2)


# =========================================================
# CANDIDATE GENERATION
# =========================================================

def generate_candidate(regular_weights):
    regular_numbers = weighted_choice_no_replace(
        candidates=list(REGULAR_RANGE),
        weights=[regular_weights[n] for n in REGULAR_RANGE],
        k=5
    )

    regular_numbers = sorted(regular_numbers)

    return regular_numbers


def generate_predictions(
    simulation_count=SIMULATION_COUNT,
    top_n=TOP_PREDICTIONS,
):
    df = load_daily_lotto_features()

    regular_weights = build_number_weights(df)
    pair_counter = build_pair_scores(df)
    pattern_distributions = build_pattern_distributions(df)

    history_sets = [
        set(get_regular_numbers(row))
        for _, row in df.iterrows()
    ]

    candidates = []

    attempts = 0
    max_attempts = simulation_count * 25

    while len(candidates) < simulation_count and attempts < max_attempts:
        attempts += 1

        numbers = generate_candidate(regular_weights)

        if has_too_much_history_overlap(numbers, history_sets):
            continue

        if consecutive_pairs(numbers) > 2:
            continue

        high_count, low_count = count_high_low(numbers)
        odd_count, even_count = count_odd_even(numbers)

        regular_sum = sum(numbers)

        if regular_sum < 45 or regular_sum > 145:
            continue

        base_score = sum(regular_weights[n] for n in numbers)
        pair_score = score_pair_strength(numbers, pair_counter)
        pattern_score = score_pattern_fit(numbers, pattern_distributions)

        raw_score = (
            base_score
            + (WEIGHT_PAIR * pair_score)
            + (WEIGHT_PATTERN * pattern_score)
        )

        candidates.append({
            "N1": numbers[0],
            "N2": numbers[1],
            "N3": numbers[2],
            "N4": numbers[3],
            "N5": numbers[4],
            "RegularSum": regular_sum,
            "HighCount": high_count,
            "LowCount": low_count,
            "OddCount": odd_count,
            "EvenCount": even_count,
            "ConsecutivePairs": consecutive_pairs(numbers),
            "RawScore": raw_score,
        })

    if not candidates:
        raise ValueError("No candidates generated. Relax the model filters.")

    candidate_df = pd.DataFrame(candidates)

    candidate_df = candidate_df.drop_duplicates(
        subset=["N1", "N2", "N3", "N4", "N5"]
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
        ].iloc[0]

        final_rows.append({
            "PredictionRank": rank,
            "N1": candidate[0],
            "N2": candidate[1],
            "N3": candidate[2],
            "N4": candidate[3],
            "N5": candidate[4],
            "RegularSum": int(match["RegularSum"]),
            "HighCount": int(match["HighCount"]),
            "LowCount": int(match["LowCount"]),
            "OddCount": int(match["OddCount"]),
            "EvenCount": int(match["EvenCount"]),
            "ConsecutivePairs": int(match["ConsecutivePairs"]),
            "RawScore": round(float(match["RawScore"]), 4),
            "Confidence": float(match["Confidence"]),
            "ModelVersion": "DailyLotto_v1_statistical",
            "GeneratedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    final_df = pd.DataFrame(final_rows)

    return final_df


# =========================================================
# EXPORT
# =========================================================

def export_daily_lotto_predictions(
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
            sheet_name="Daily_Lotto_Predictions",
            index=False
        )

    print("\nDaily Lotto predictions exported.")
    print(f"Rows: {len(predictions)}")
    print(f"File: {OUTPUT_FILE}")

    return predictions


# =========================================================
# CLI
# =========================================================

def main():
    export_daily_lotto_predictions()


if __name__ == "__main__":
    main()