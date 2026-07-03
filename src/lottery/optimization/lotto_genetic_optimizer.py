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
EXPORT_DIR = BASE_DIR / "data" / "exports" / "optimization"
OUTPUT_FILE = EXPORT_DIR / "lotto_genetic_optimizer_results.xlsx"

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

LOW_HIGH_MIDPOINT = CURRENT_RULE.regular_max // 2
RANGE_BUCKETS = get_dynamic_buckets(CURRENT_RULE)
UPPER_START = get_upper_start(CURRENT_RULE)
UPPER_ELITE = get_upper_elite(CURRENT_RULE)

POPULATION_SIZE = 300
GENERATIONS = 70
MUTATION_RATE = 0.22
ELITE_RATIO = 0.12
TARGET_POPULATION = 120
RNG_SEED = 42
_rng = np.random.default_rng(RNG_SEED)

MIN_REGULAR_SUM = int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT * 0.30)
MAX_REGULAR_SUM = int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT * 0.88)


def load_lotto_features() -> pd.DataFrame:
    if not FEATURES_FILE.exists():
        raise FileNotFoundError(f"Missing feature file:\n{FEATURES_FILE}")

    df = pd.read_excel(FEATURES_FILE, sheet_name="Lotto_Features", engine="openpyxl")
    df["DrawDate"] = pd.to_datetime(df["DrawDate"], errors="coerce")

    number_cols = REGULAR_COLS + ([BONUS_COL] if BONUS_COL in df.columns else [])
    for col in number_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["DrawDate"] + REGULAR_COLS)
    if "GameName" in df.columns:
        df = df[df["GameName"].astype(str).str.strip().str.lower() == GAME_NAME.lower()].copy()

    return df.sort_values(by="DrawDate", ascending=False).reset_index(drop=True)


def get_regular_numbers(row) -> list[int]:
    return [int(row[col]) for col in REGULAR_COLS if col in row and pd.notna(row[col])]


def get_bonus_number(row) -> int | None:
    if BONUS_COL not in row or pd.isna(row[BONUS_COL]):
        return None
    return int(row[BONUS_COL])


def count_high_low(numbers):
    low = sum(1 for n in numbers if n <= LOW_HIGH_MIDPOINT)
    return len(numbers) - low, low


def count_odd_even(numbers):
    odd = sum(1 for n in numbers if n % 2 != 0)
    return odd, len(numbers) - odd


def count_consecutive(numbers):
    numbers = sorted(numbers)
    return sum(1 for i in range(len(numbers) - 1) if numbers[i + 1] - numbers[i] == 1)


def number_entropy(numbers):
    numbers = sorted(numbers)
    gaps = [numbers[i + 1] - numbers[i] for i in range(len(numbers) - 1)]
    return 0 if not gaps else float(np.std(gaps))


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
    score = occupied_buckets * 5
    if max_bucket_count <= 3:
        score += 8
    if bucket_counts["HIGH"] >= 1:
        score += 12
    if bucket_counts["HIGH"] >= 2:
        score += 10
    if bucket_counts["LOW"] >= 1 and bucket_counts["HIGH"] >= 1:
        score += 6
    return score


def upper_range_score(numbers):
    count_upper = sum(1 for n in numbers if n >= UPPER_START)
    count_elite = sum(1 for n in numbers if n >= UPPER_ELITE)
    score = 0
    if count_upper >= 1:
        score += 12
    if count_upper >= 2:
        score += 10
    if count_elite >= 1:
        score += 7
    return score


def build_frequency_scores(df):
    counter = Counter()
    for _, row in df.iterrows():
        for n in get_regular_numbers(row):
            if n in HISTORICAL_REGULAR_RANGE:
                counter[n] += 1
    return counter


def build_pair_scores(df):
    pair_counter = Counter()
    for _, row in df.iterrows():
        nums = sorted(n for n in get_regular_numbers(row) if n in HISTORICAL_REGULAR_RANGE)
        for pair in combinations(nums, 2):
            pair_counter[pair] += 1
    return pair_counter


def build_hot_numbers(df, top_n=12):
    counter = build_frequency_scores(df)
    return set([n for n, _ in counter.most_common(top_n)])


def build_history_sets(df):
    return [set(get_regular_numbers(row)) for _, row in df.iterrows()]


def random_genome():
    regulars = sorted(_rng.choice(list(PREDICTION_REGULAR_RANGE), size=REGULAR_PICK_COUNT, replace=False).tolist())

    if HAS_BONUS:
        bonus_pool = [n for n in PREDICTION_BONUS_RANGE if n not in regulars]
        bonus = int(_rng.choice(bonus_pool, size=1)[0])
    else:
        bonus = None

    return {"regulars": regulars, "bonus": bonus}


def fitness_score(genome, freq_counter, pair_counter, hot_numbers, history_sets):
    regulars = genome["regulars"]
    score = 0.0

    freq_values = [freq_counter[n] for n in regulars]
    score += float(np.mean(freq_values)) * 0.35

    high, low = count_high_low(regulars)
    if (high, low) in [(3, 3), (4, 2), (2, 4)]:
        score += 8

    odd, even = count_odd_even(regulars)
    if (odd, even) in [(3, 3), (4, 2), (2, 4)]:
        score += 8

    total = sum(regulars)
    if MIN_REGULAR_SUM <= total <= MAX_REGULAR_SUM:
        score += 14
    elif int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT * 0.25) <= total <= int(CURRENT_RULE.regular_max * REGULAR_PICK_COUNT * 0.95):
        score += 8

    consecutive = count_consecutive(regulars)
    if consecutive == 0:
        score += 8
    elif consecutive == 1:
        score += 5
    elif consecutive >= 3:
        score -= 12

    score += number_entropy(regulars) * 2.8
    score += bucket_balance_score(regulars) * 1.4
    score += upper_range_score(regulars) * 1.7
    score += sum(pair_counter[pair] for pair in combinations(sorted(regulars), 2)) * 0.025

    hot_overlap = sum(1 for n in regulars if n in hot_numbers)
    score -= hot_overlap * 1.2

    regular_set = set(regulars)
    for hist in history_sets:
        overlap = len(regular_set.intersection(hist))
        if overlap >= REGULAR_PICK_COUNT:
            score -= 120
        elif overlap == REGULAR_PICK_COUNT - 1:
            score -= 20

    return score + 1


def mutate(genome):
    genome = {"regulars": genome["regulars"][:], "bonus": genome["bonus"]}

    if _rng.random() < MUTATION_RATE:
        idx = _rng.integers(0, REGULAR_PICK_COUNT)
        available = [n for n in PREDICTION_REGULAR_RANGE if n not in genome["regulars"]]
        genome["regulars"][idx] = int(_rng.choice(available))
        genome["regulars"] = sorted(list(set(genome["regulars"])))

        while len(genome["regulars"]) < REGULAR_PICK_COUNT:
            candidate = int(_rng.choice(list(PREDICTION_REGULAR_RANGE)))
            if candidate not in genome["regulars"]:
                genome["regulars"].append(candidate)
        genome["regulars"] = sorted(genome["regulars"])

    if HAS_BONUS and _rng.random() < MUTATION_RATE:
        bonus_pool = [n for n in PREDICTION_BONUS_RANGE if n not in genome["regulars"]]
        genome["bonus"] = int(_rng.choice(bonus_pool))

    return genome


def crossover(parent1, parent2):
    combined = list(set(parent1["regulars"] + parent2["regulars"]))
    while len(combined) < REGULAR_PICK_COUNT:
        candidate = int(_rng.choice(list(PREDICTION_REGULAR_RANGE)))
        if candidate not in combined:
            combined.append(candidate)

    regulars = sorted(_rng.choice(combined, size=REGULAR_PICK_COUNT, replace=False).tolist())

    if HAS_BONUS:
        bonus = int(_rng.choice([parent1["bonus"], parent2["bonus"]]))
        if bonus in regulars:
            bonus_pool = [n for n in PREDICTION_BONUS_RANGE if n not in regulars]
            bonus = int(_rng.choice(bonus_pool))
    else:
        bonus = None

    return mutate({"regulars": regulars, "bonus": bonus})


def run_lotto_genetic_optimizer():
    df = load_lotto_features()
    freq_counter = build_frequency_scores(df)
    pair_counter = build_pair_scores(df)
    hot_numbers = build_hot_numbers(df)
    history_sets = build_history_sets(df)

    population = [random_genome() for _ in range(POPULATION_SIZE)]
    generation_rows = []

    print("\n======================================")
    print("LOTTO GENETIC OPTIMIZER V3")
    print("======================================")
    print(f"Population Size : {POPULATION_SIZE}")
    print(f"Generations     : {GENERATIONS}")
    print(f"Mode            : Rules-aware {CURRENT_RULE.regular_min}-{CURRENT_RULE.regular_max}")
    print("======================================\n")

    for generation in range(1, GENERATIONS + 1):
        scored_population = []
        for genome in population:
            score = fitness_score(genome, freq_counter, pair_counter, hot_numbers, history_sets)
            scored_population.append({"genome": genome, "score": score})

        scored_population = sorted(scored_population, key=lambda x: x["score"], reverse=True)
        best_score = scored_population[0]["score"]
        avg_score = np.mean([x["score"] for x in scored_population])
        generation_rows.append({"Generation": generation, "BestScore": round(best_score, 4), "AverageScore": round(avg_score, 4)})

        if generation % 5 == 0:
            print(f"Generation {generation:<3} | Best Score: {best_score:.2f} | Avg Score: {avg_score:.2f}")

        elite_count = max(2, int(POPULATION_SIZE * ELITE_RATIO))
        elites = scored_population[:elite_count]
        next_population = [x["genome"] for x in elites]

        while len(next_population) < POPULATION_SIZE:
            parent1 = _rng.choice(elites)["genome"]
            parent2 = _rng.choice(elites)["genome"]
            next_population.append(crossover(parent1, parent2))

        population = next_population

    final_population = []
    for genome in population:
        score = fitness_score(genome, freq_counter, pair_counter, hot_numbers, history_sets)
        final_population.append({"Genome": genome, "FitnessScore": score})

    final_population = sorted(final_population, key=lambda x: x["FitnessScore"], reverse=True)
    unique = set()
    rows = []

    for item in final_population:
        genome = item["Genome"]
        regulars = genome["regulars"]

        if sum(1 for n in regulars if n >= UPPER_START) == 0:
            continue

        key = tuple(regulars + ([genome["bonus"]] if HAS_BONUS else []))
        if key in unique:
            continue
        unique.add(key)

        bucket_counts = count_bucket_numbers(regulars)
        row = {
            "Rank": len(rows) + 1,
            **{f"N{i + 1}": regulars[i] for i in range(REGULAR_PICK_COUNT)},
            "RegularSum": sum(regulars),
            "HighCount": count_high_low(regulars)[0],
            "LowCount": count_high_low(regulars)[1],
            "OddCount": count_odd_even(regulars)[0],
            "EvenCount": count_odd_even(regulars)[1],
            "Bucket_LOW": bucket_counts["LOW"],
            "Bucket_MID_LOW": bucket_counts["MID_LOW"],
            "Bucket_MID_HIGH": bucket_counts["MID_HIGH"],
            "Bucket_HIGH": bucket_counts["HIGH"],
            "UpperRangeCount": sum(1 for n in regulars if n >= UPPER_START),
            "ConsecutivePairs": count_consecutive(regulars),
            "EntropyScore": round(number_entropy(regulars), 4),
            "FitnessScore": round(item["FitnessScore"], 4),
            "RuleVersion": CURRENT_RULE.rule_version,
            "ModelVersion": "LottoGeneticOptimizer_v3_rules_aware",
            "GeneratedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if HAS_BONUS:
            row["Bonus"] = genome["bonus"]
        rows.append(row)

        if len(rows) >= TARGET_POPULATION:
            break

    results_df = pd.DataFrame(rows)
    generation_df = pd.DataFrame(generation_rows)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl", mode="w") as writer:
        results_df.to_excel(writer, sheet_name="Optimized_Numbers", index=False)
        generation_df.to_excel(writer, sheet_name="Generation_Scores", index=False)

    print("\n======================================")
    print("LOTTO GENETIC OPTIMIZATION COMPLETE")
    print("======================================")
    print(f"Rows exported : {len(results_df)}")
    print(f"File          : {OUTPUT_FILE}")
    print("======================================\n")

    return results_df


def main():
    run_lotto_genetic_optimizer()


if __name__ == "__main__":
    main()
