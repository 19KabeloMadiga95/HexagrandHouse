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

FEATURES_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "daily_lotto_features.xlsx"
)

EXPORT_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "optimization"
)

OUTPUT_FILE = (
    EXPORT_DIR
    / "daily_lotto_genetic_optimizer_results.xlsx"
)


# =========================================================
# CONFIG
# =========================================================

REGULAR_RANGE = range(1, 37)

POPULATION_SIZE = 250
GENERATIONS = 60

MUTATION_RATE = 0.18
ELITE_RATIO = 0.12

TARGET_POPULATION = 120

RNG_SEED = 42
_rng = np.random.default_rng(RNG_SEED)


# =========================================================
# LOAD DATA
# =========================================================

def load_daily_lotto_features():
    if not FEATURES_FILE.exists():
        raise FileNotFoundError(
            f"Missing feature file:\n{FEATURES_FILE}"
        )

    df = pd.read_excel(
        FEATURES_FILE,
        sheet_name="Daily_Lotto_Features",
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


# =========================================================
# HELPERS
# =========================================================

def get_regular_numbers(row):
    return [
        int(row["N1"]),
        int(row["N2"]),
        int(row["N3"]),
        int(row["N4"]),
        int(row["N5"]),
    ]


def count_high_low(numbers):
    low = sum(1 for n in numbers if n <= 18)
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
        gaps.append(
            numbers[i + 1] - numbers[i]
        )

    if not gaps:
        return 0

    return np.std(gaps)


# =========================================================
# LEARNING
# =========================================================

def build_frequency_scores(df):
    counter = Counter()

    for _, row in df.iterrows():
        for n in get_regular_numbers(row):
            counter[n] += 1

    return counter


def build_pair_scores(df):
    pair_counter = Counter()

    for _, row in df.iterrows():
        nums = sorted(
            get_regular_numbers(row)
        )

        for pair in combinations(nums, 2):
            pair_counter[pair] += 1

    return pair_counter


def build_hot_numbers(df, top_n=10):
    counter = build_frequency_scores(df)

    return set([
        n for n, _ in counter.most_common(top_n)
    ])


def build_history_sets(df):
    history = []

    for _, row in df.iterrows():
        history.append(
            set(get_regular_numbers(row))
        )

    return history


# =========================================================
# GENOME
# =========================================================

def random_genome():
    regulars = sorted(
        _rng.choice(
            np.arange(1, 37),
            size=5,
            replace=False
        ).tolist()
    )

    return {
        "regulars": regulars,
    }


# =========================================================
# FITNESS
# =========================================================

def fitness_score(
    genome,
    freq_counter,
    pair_counter,
    hot_numbers,
    history_sets,
):
    regulars = genome["regulars"]

    score = 0

    # Frequency balance
    freq_values = [
        freq_counter[n]
        for n in regulars
    ]

    avg_freq = np.mean(freq_values)

    score += avg_freq * 0.7

    # High / low
    high, low = count_high_low(regulars)

    if (high, low) in [(2, 3), (3, 2)]:
        score += 10

    elif (high, low) in [(1, 4), (4, 1)]:
        score += 4

    # Odd / even
    odd, even = count_odd_even(regulars)

    if (odd, even) in [(2, 3), (3, 2)]:
        score += 10

    elif (odd, even) in [(1, 4), (4, 1)]:
        score += 4

    # Sum balance
    total = sum(regulars)

    if 70 <= total <= 110:
        score += 12

    elif 45 <= total <= 145:
        score += 6

    # Consecutives
    consecutive = count_consecutive(regulars)

    if consecutive == 0:
        score += 8

    elif consecutive == 1:
        score += 4

    elif consecutive >= 3:
        score -= 12

    # Entropy
    entropy = number_entropy(regulars)

    score += entropy * 2.5

    # Pair scoring
    pair_score = 0

    for pair in combinations(
        sorted(regulars),
        2
    ):
        pair_score += pair_counter[pair]

    score += pair_score * 0.05

    # Anti-crowding
    hot_overlap = sum(
        1 for n in regulars
        if n in hot_numbers
    )

    score -= hot_overlap * 2

    # Historical duplication
    regular_set = set(regulars)

    for hist in history_sets:
        overlap = len(
            regular_set.intersection(hist)
        )

        if overlap >= 5:
            score -= 120

        elif overlap == 4:
            score -= 20

    return score


# =========================================================
# EVOLUTION
# =========================================================

def mutate(genome):
    genome = {
        "regulars": genome["regulars"][:],
    }

    if _rng.random() < MUTATION_RATE:
        idx = _rng.integers(0, 5)

        available = [
            n for n in REGULAR_RANGE
            if n not in genome["regulars"]
        ]

        genome["regulars"][idx] = int(
            _rng.choice(available)
        )

        genome["regulars"] = sorted(
            list(set(genome["regulars"]))
        )

        while len(genome["regulars"]) < 5:
            candidate = int(
                _rng.choice(list(REGULAR_RANGE))
            )

            if candidate not in genome["regulars"]:
                genome["regulars"].append(candidate)

        genome["regulars"] = sorted(
            genome["regulars"]
        )

    return genome


def crossover(parent1, parent2):
    combined = list(
        set(
            parent1["regulars"]
            + parent2["regulars"]
        )
    )

    if len(combined) < 5:
        while len(combined) < 5:
            candidate = int(
                _rng.choice(
                    list(REGULAR_RANGE)
                )
            )

            if candidate not in combined:
                combined.append(candidate)

    regulars = sorted(
        _rng.choice(
            combined,
            size=5,
            replace=False
        ).tolist()
    )

    child = {
        "regulars": regulars,
    }

    return mutate(child)


# =========================================================
# MAIN OPTIMIZER
# =========================================================

def run_daily_lotto_genetic_optimizer():
    df = load_daily_lotto_features()

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
    print("DAILY LOTTO GENETIC OPTIMIZER")
    print("======================================")
    print(f"Population Size : {POPULATION_SIZE}")
    print(f"Generations     : {GENERATIONS}")
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

        elite_count = int(
            POPULATION_SIZE * ELITE_RATIO
        )

        elites = scored_population[:elite_count]

        next_population = [
            x["genome"]
            for x in elites
        ]

        while len(next_population) < POPULATION_SIZE:
            parent1 = _rng.choice(elites)["genome"]
            parent2 = _rng.choice(elites)["genome"]

            child = crossover(
                parent1,
                parent2
            )

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

        key = tuple(
            genome["regulars"]
        )

        if key in unique:
            continue

        unique.add(key)

        regulars = genome["regulars"]

        rows.append({
            "Rank": len(rows) + 1,
            "N1": regulars[0],
            "N2": regulars[1],
            "N3": regulars[2],
            "N4": regulars[3],
            "N5": regulars[4],
            "RegularSum": sum(regulars),
            "HighCount": count_high_low(regulars)[0],
            "LowCount": count_high_low(regulars)[1],
            "OddCount": count_odd_even(regulars)[0],
            "EvenCount": count_odd_even(regulars)[1],
            "ConsecutivePairs": count_consecutive(regulars),
            "EntropyScore": round(
                number_entropy(regulars),
                4
            ),
            "FitnessScore": round(
                item["FitnessScore"],
                4
            ),
            "ModelVersion": "DailyLottoGeneticOptimizer_v1",
            "GeneratedAt": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        })

        if len(rows) >= TARGET_POPULATION:
            break

    results_df = pd.DataFrame(rows)

    generation_df = pd.DataFrame(
        generation_rows
    )

    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

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
    print("DAILY LOTTO GENETIC OPTIMIZATION COMPLETE")
    print("======================================")
    print(f"Rows exported : {len(results_df)}")
    print(f"File          : {OUTPUT_FILE}")
    print("======================================\n")

    return results_df


# =========================================================
# CLI
# =========================================================

def main():
    run_daily_lotto_genetic_optimizer()


if __name__ == "__main__":
    main()