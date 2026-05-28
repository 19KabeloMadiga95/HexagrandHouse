from pathlib import Path
from collections import Counter
from itertools import combinations
from datetime import datetime

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]

FEATURES_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "lotto_features.xlsx"
)

EXPORT_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "optimization"
)

OUTPUT_FILE = (
    EXPORT_DIR
    / "lotto_genetic_optimizer_results.xlsx"
)


REGULAR_RANGE = range(1, 59)
BONUS_RANGE = range(1, 59)

POST_EXPANSION_DATE = pd.Timestamp("2025-09-01")

POPULATION_SIZE = 300
GENERATIONS = 70

MUTATION_RATE = 0.22
ELITE_RATIO = 0.12

TARGET_POPULATION = 120

RNG_SEED = 42
_rng = np.random.default_rng(RNG_SEED)

RANGE_BUCKETS = {
    "LOW": range(1, 15),
    "MID_LOW": range(15, 30),
    "MID_HIGH": range(30, 45),
    "HIGH": range(45, 59),
}


def load_lotto_features():
    if not FEATURES_FILE.exists():
        raise FileNotFoundError(
            f"Missing feature file:\n{FEATURES_FILE}"
        )

    df = pd.read_excel(
        FEATURES_FILE,
        sheet_name="Lotto_Features",
        engine="openpyxl"
    )

    df["DrawDate"] = pd.to_datetime(
        df["DrawDate"],
        errors="coerce"
    )

    number_cols = [
        "N1",
        "N2",
        "N3",
        "N4",
        "N5",
        "N6",
        "Bonus",
    ]

    for col in number_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna(
        subset=["DrawDate"] + number_cols
    )

    df = df.sort_values(
        by="DrawDate",
        ascending=False
    ).reset_index(drop=True)

    return df


def era_weight(draw_date):
    if pd.isna(draw_date):
        return 0.50

    if draw_date >= POST_EXPANSION_DATE:
        return 3.0

    return 0.45


def get_regular_numbers(row):
    return [
        int(row["N1"]),
        int(row["N2"]),
        int(row["N3"]),
        int(row["N4"]),
        int(row["N5"]),
        int(row["N6"]),
    ]


def count_high_low(numbers):
    low = sum(1 for n in numbers if n <= 29)
    high = len(numbers) - low

    return high, low


def count_odd_even(numbers):
    odd = sum(1 for n in numbers if n % 2 != 0)
    even = len(numbers) - odd

    return odd, even


def count_consecutive(numbers):
    numbers = sorted(numbers)
    count = 0

    for i in range(len(numbers) - 1):
        if numbers[i + 1] - numbers[i] == 1:
            count += 1

    return count


def number_entropy(numbers):
    numbers = sorted(numbers)

    gaps = []

    for i in range(len(numbers) - 1):
        gaps.append(numbers[i + 1] - numbers[i])

    if not gaps:
        return 0

    return np.std(gaps)


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

    score += occupied_buckets * 5

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
    count_50_plus = sum(1 for n in numbers if n >= 50)
    count_53_plus = sum(1 for n in numbers if n >= 53)

    score = 0

    if count_50_plus >= 1:
        score += 12

    if count_50_plus >= 2:
        score += 10

    if count_53_plus >= 1:
        score += 7

    return score


def build_frequency_scores(df):
    counter = Counter()

    for _, row in df.iterrows():
        weight = era_weight(row["DrawDate"])

        for n in get_regular_numbers(row):
            counter[n] += weight

    return counter


def build_pair_scores(df):
    pair_counter = Counter()

    for _, row in df.iterrows():
        weight = era_weight(row["DrawDate"])
        nums = sorted(get_regular_numbers(row))

        for pair in combinations(nums, 2):
            pair_counter[pair] += weight

    return pair_counter


def build_hot_numbers(df, top_n=12):
    counter = build_frequency_scores(df)

    return set([
        n for n, _ in counter.most_common(top_n)
    ])


def build_history_sets(df):
    history = []

    for _, row in df.iterrows():
        history.append(set(get_regular_numbers(row)))

    return history


def random_genome():
    regulars = sorted(
        _rng.choice(
            np.arange(1, 59),
            size=6,
            replace=False
        ).tolist()
    )

    bonus_pool = [
        n for n in range(1, 59)
        if n not in regulars
    ]

    bonus = int(
        _rng.choice(
            bonus_pool,
            size=1
        )[0]
    )

    return {
        "regulars": regulars,
        "bonus": bonus,
    }


def fitness_score(
    genome,
    freq_counter,
    pair_counter,
    hot_numbers,
    history_sets,
):
    regulars = genome["regulars"]

    score = 0

    freq_values = [
        freq_counter[n]
        for n in regulars
    ]

    avg_freq = np.mean(freq_values)

    score += avg_freq * 0.35

    high, low = count_high_low(regulars)

    if (high, low) in [(3, 3), (4, 2), (2, 4)]:
        score += 8

    odd, even = count_odd_even(regulars)

    if (odd, even) in [(3, 3), (4, 2), (2, 4)]:
        score += 8

    total = sum(regulars)

    if 130 <= total <= 230:
        score += 14

    elif 105 <= total <= 260:
        score += 8

    elif 90 <= total <= 285:
        score += 3

    consecutive = count_consecutive(regulars)

    if consecutive == 0:
        score += 8

    elif consecutive == 1:
        score += 5

    elif consecutive >= 3:
        score -= 12

    entropy = number_entropy(regulars)
    score += entropy * 2.8

    bucket_score = bucket_balance_score(regulars)
    score += bucket_score * 1.4

    upper_score = upper_range_score(regulars)
    score += upper_score * 1.7

    pair_score = 0

    for pair in combinations(sorted(regulars), 2):
        pair_score += pair_counter[pair]

    score += pair_score * 0.025

    hot_overlap = sum(
        1 for n in regulars
        if n in hot_numbers
    )

    score -= hot_overlap * 1.2

    regular_set = set(regulars)

    for hist in history_sets:
        overlap = len(regular_set.intersection(hist))

        if overlap >= 6:
            score -= 120

        elif overlap == 5:
            score -= 20

    score += 1

    return score


def mutate(genome):
    genome = {
        "regulars": genome["regulars"][:],
        "bonus": genome["bonus"],
    }

    if _rng.random() < MUTATION_RATE:
        idx = _rng.integers(0, 6)

        available = [
            n for n in REGULAR_RANGE
            if n not in genome["regulars"]
        ]

        genome["regulars"][idx] = int(
            _rng.choice(available)
        )

        genome["regulars"] = sorted(list(set(genome["regulars"])))

        while len(genome["regulars"]) < 6:
            candidate = int(_rng.choice(list(REGULAR_RANGE)))

            if candidate not in genome["regulars"]:
                genome["regulars"].append(candidate)

        genome["regulars"] = sorted(genome["regulars"])

    if _rng.random() < MUTATION_RATE:
        bonus_pool = [
            n for n in BONUS_RANGE
            if n not in genome["regulars"]
        ]

        genome["bonus"] = int(_rng.choice(bonus_pool))

    return genome


def crossover(parent1, parent2):
    combined = list(
        set(
            parent1["regulars"]
            + parent2["regulars"]
        )
    )

    if len(combined) < 6:
        while len(combined) < 6:
            candidate = int(_rng.choice(list(REGULAR_RANGE)))

            if candidate not in combined:
                combined.append(candidate)

    regulars = sorted(
        _rng.choice(
            combined,
            size=6,
            replace=False
        ).tolist()
    )

    bonus = int(
        _rng.choice([
            parent1["bonus"],
            parent2["bonus"]
        ])
    )

    if bonus in regulars:
        bonus_pool = [
            n for n in BONUS_RANGE
            if n not in regulars
        ]

        bonus = int(_rng.choice(bonus_pool))

    child = {
        "regulars": regulars,
        "bonus": bonus,
    }

    return mutate(child)


def run_lotto_genetic_optimizer():
    df = load_lotto_features()

    freq_counter = build_frequency_scores(df)
    pair_counter = build_pair_scores(df)
    hot_numbers = build_hot_numbers(df)
    history_sets = build_history_sets(df)

    population = [
        random_genome()
        for _ in range(POPULATION_SIZE)
    ]

    generation_rows = []

    print("\n======================================")
    print("LOTTO GENETIC OPTIMIZER V2")
    print("======================================")
    print(f"Population Size : {POPULATION_SIZE}")
    print(f"Generations     : {GENERATIONS}")
    print("Mode            : Range-balanced 1-58")
    print("======================================\n")

    for generation in range(1, GENERATIONS + 1):
        scored_population = []

        for genome in population:
            score = fitness_score(
                genome=genome,
                freq_counter=freq_counter,
                pair_counter=pair_counter,
                hot_numbers=hot_numbers,
                history_sets=history_sets,
            )

            scored_population.append({
                "genome": genome,
                "score": score,
            })

        scored_population = sorted(
            scored_population,
            key=lambda x: x["score"],
            reverse=True
        )

        best_score = scored_population[0]["score"]

        avg_score = np.mean([
            x["score"]
            for x in scored_population
        ])

        generation_rows.append({
            "Generation": generation,
            "BestScore": round(best_score, 4),
            "AverageScore": round(avg_score, 4),
        })

        if generation % 5 == 0:
            print(
                f"Generation {generation:<3} | "
                f"Best Score: {best_score:.2f} | "
                f"Avg Score: {avg_score:.2f}"
            )

        elite_count = int(POPULATION_SIZE * ELITE_RATIO)
        elites = scored_population[:elite_count]

        next_population = [
            x["genome"]
            for x in elites
        ]

        while len(next_population) < POPULATION_SIZE:
            parent1 = _rng.choice(elites)["genome"]
            parent2 = _rng.choice(elites)["genome"]

            child = crossover(parent1, parent2)

            next_population.append(child)

        population = next_population

    final_population = []

    for genome in population:
        score = fitness_score(
            genome=genome,
            freq_counter=freq_counter,
            pair_counter=pair_counter,
            hot_numbers=hot_numbers,
            history_sets=history_sets,
        )

        final_population.append({
            "Genome": genome,
            "FitnessScore": score,
        })

    final_population = sorted(
        final_population,
        key=lambda x: x["FitnessScore"],
        reverse=True
    )

    unique = set()
    rows = []

    for item in final_population:
        genome = item["Genome"]
        regulars = genome["regulars"]

        if sum(1 for n in regulars if n >= 45) == 0:
            continue

        key = tuple(regulars + [genome["bonus"]])

        if key in unique:
            continue

        unique.add(key)

        bucket_counts = count_bucket_numbers(regulars)

        rows.append({
            "Rank": len(rows) + 1,
            "N1": regulars[0],
            "N2": regulars[1],
            "N3": regulars[2],
            "N4": regulars[3],
            "N5": regulars[4],
            "N6": regulars[5],
            "Bonus": genome["bonus"],
            "RegularSum": sum(regulars),
            "HighCount": count_high_low(regulars)[0],
            "LowCount": count_high_low(regulars)[1],
            "OddCount": count_odd_even(regulars)[0],
            "EvenCount": count_odd_even(regulars)[1],
            "Bucket_LOW": bucket_counts["LOW"],
            "Bucket_MID_LOW": bucket_counts["MID_LOW"],
            "Bucket_MID_HIGH": bucket_counts["MID_HIGH"],
            "Bucket_HIGH": bucket_counts["HIGH"],
            "Upper50PlusCount": sum(1 for n in regulars if n >= 50),
            "ConsecutivePairs": count_consecutive(regulars),
            "EntropyScore": round(number_entropy(regulars), 4),
            "FitnessScore": round(item["FitnessScore"], 4),
            "ModelVersion": "LottoGeneticOptimizer_v2_range_balanced",
            "GeneratedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        if len(rows) >= TARGET_POPULATION:
            break

    results_df = pd.DataFrame(rows)
    generation_df = pd.DataFrame(generation_rows)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        results_df.to_excel(
            writer,
            sheet_name="Optimized_Numbers",
            index=False
        )

        generation_df.to_excel(
            writer,
            sheet_name="Generation_Scores",
            index=False
        )

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