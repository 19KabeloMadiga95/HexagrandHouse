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

POWERBALL_FEATURES = (
    BASE_DIR
    / "data"
    / "processed"
    / "features"
    / "powerball_features.xlsx"
)

GENETIC_RESULTS = (
    BASE_DIR
    / "data"
    / "exports"
    / "optimization"
    / "powerball_genetic_optimizer_results.xlsx"
)

BACKTEST_RESULTS = (
    BASE_DIR
    / "data"
    / "exports"
    / "backtesting"
    / "powerball_model_comparison_backtest.xlsx"
)

EXPORT_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "optimization"
)

OUTPUT_FILE = (
    EXPORT_DIR
    / "ensemble_predictions.xlsx"
)


# =========================================================
# CONFIG
# =========================================================

REGULAR_RANGE = range(1, 51)
BONUS_RANGE = range(1, 21)

TOP_GENETIC_ROWS = 80
TOP_BACKTEST_MODELS = 3

FINAL_OUTPUT_ROWS = 25

RNG_SEED = 42
_rng = np.random.default_rng(RNG_SEED)


# =========================================================
# LOADERS
# =========================================================

def load_powerball_history():
    if not POWERBALL_FEATURES.exists():
        raise FileNotFoundError(
            f"Missing file:\n{POWERBALL_FEATURES}"
        )

    df = pd.read_excel(
        POWERBALL_FEATURES,
        sheet_name="PowerBall_Features",
        engine="openpyxl"
    )

    number_cols = [
        "N1", "N2", "N3", "N4", "N5", "Bonus"
    ]

    for col in number_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna(
        subset=number_cols
    )

    return df


def load_genetic_results():
    if not GENETIC_RESULTS.exists():
        raise FileNotFoundError(
            f"Missing file:\n{GENETIC_RESULTS}"
        )

    df = pd.read_excel(
        GENETIC_RESULTS,
        sheet_name="Optimized_Numbers",
        engine="openpyxl"
    )

    return df.head(TOP_GENETIC_ROWS)


def load_backtest_summary():
    if not BACKTEST_RESULTS.exists():
        raise FileNotFoundError(
            f"Missing file:\n{BACKTEST_RESULTS}"
        )

    df = pd.read_excel(
        BACKTEST_RESULTS,
        sheet_name="Summary",
        engine="openpyxl"
    )

    return df


# =========================================================
# HELPERS
# =========================================================

def regulars_from_row(row):
    return [
        int(row["N1"]),
        int(row["N2"]),
        int(row["N3"]),
        int(row["N4"]),
        int(row["N5"]),
    ]


def count_high_low(numbers):
    low = sum(1 for n in numbers if n <= 25)
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


def entropy_score(numbers):
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
# HISTORY LEARNING
# =========================================================

def build_frequency_scores(df):
    counter = Counter()

    for _, row in df.iterrows():
        for n in regulars_from_row(row):
            counter[n] += 1

    return counter


def build_pair_scores(df):
    pair_counter = Counter()

    for _, row in df.iterrows():
        nums = sorted(
            regulars_from_row(row)
        )

        for pair in combinations(nums, 2):
            pair_counter[pair] += 1

    return pair_counter


def build_recent_numbers(df, recent_draws=20):
    recent_df = df.head(recent_draws)

    recent_numbers = set()

    for _, row in recent_df.iterrows():
        for n in regulars_from_row(row):
            recent_numbers.add(n)

    return recent_numbers


def build_history_sets(df):
    history = []

    for _, row in df.iterrows():
        history.append(
            set(regulars_from_row(row))
        )

    return history


# =========================================================
# ENSEMBLE SCORING
# =========================================================

def pair_strength(numbers, pair_counter):
    score = 0

    for pair in combinations(
        sorted(numbers),
        2
    ):
        score += pair_counter[pair]

    return score


def historical_overlap_penalty(
    numbers,
    history_sets
):
    penalties = 0

    number_set = set(numbers)

    for hist in history_sets:
        overlap = len(
            number_set.intersection(hist)
        )

        if overlap >= 5:
            penalties += 100

        elif overlap == 4:
            penalties += 10

    return penalties


def score_candidate(
    row,
    freq_counter,
    pair_counter,
    recent_numbers,
    history_sets,
):
    numbers = regulars_from_row(row)

    score = 0

    # -----------------------------------------------------
    # Base genetic fitness
    # -----------------------------------------------------

    if "FitnessScore" in row:
        score += float(row["FitnessScore"]) * 1.8

    # -----------------------------------------------------
    # Frequency balancing
    # -----------------------------------------------------

    freq_values = [
        freq_counter[n]
        for n in numbers
    ]

    score += np.mean(freq_values) * 0.4

    # -----------------------------------------------------
    # Pair learning
    # -----------------------------------------------------

    score += pair_strength(
        numbers,
        pair_counter
    ) * 0.03

    # -----------------------------------------------------
    # Pattern balancing
    # -----------------------------------------------------

    high, low = count_high_low(numbers)

    if (high, low) in [(2, 3), (3, 2)]:
        score += 8

    odd, even = count_odd_even(numbers)

    if (odd, even) in [(2, 3), (3, 2)]:
        score += 8

    # -----------------------------------------------------
    # Sum balancing
    # -----------------------------------------------------

    total = sum(numbers)

    if 90 <= total <= 170:
        score += 10

    elif 70 <= total <= 190:
        score += 5

    # -----------------------------------------------------
    # Consecutive balancing
    # -----------------------------------------------------

    consecutive = count_consecutive(numbers)

    if consecutive == 0:
        score += 5

    elif consecutive == 1:
        score += 3

    elif consecutive >= 3:
        score -= 10

    # -----------------------------------------------------
    # Entropy
    # -----------------------------------------------------

    score += entropy_score(numbers) * 2.5

    # -----------------------------------------------------
    # Recent number moderation
    # -----------------------------------------------------

    recent_overlap = sum(
        1 for n in numbers
        if n in recent_numbers
    )

    if recent_overlap <= 2:
        score += 4

    elif recent_overlap >= 5:
        score -= 6

    # -----------------------------------------------------
    # Historical duplication penalties
    # -----------------------------------------------------

    score -= historical_overlap_penalty(
        numbers,
        history_sets
    )

    return score


# =========================================================
# MODEL ENSEMBLE
# =========================================================

def build_ensemble_candidates():
    history_df = load_powerball_history()

    genetic_df = load_genetic_results()

    backtest_df = load_backtest_summary()

    freq_counter = build_frequency_scores(
        history_df
    )

    pair_counter = build_pair_scores(
        history_df
    )

    recent_numbers = build_recent_numbers(
        history_df
    )

    history_sets = build_history_sets(
        history_df
    )

    top_models = (
        backtest_df
        .sort_values(
            by="AverageBestRegularMatch_PerDraw",
            ascending=False
        )
        .head(TOP_BACKTEST_MODELS)
    )

    top_model_names = top_models[
        "ModelName"
    ].tolist()

    print("\n======================================")
    print("ENSEMBLE PREDICTION ENGINE")
    print("======================================")
    print(f"Top Backtest Models: {top_model_names}")
    print("======================================\n")

    scored_rows = []

    for _, row in genetic_df.iterrows():
        ensemble_score = score_candidate(
            row=row,
            freq_counter=freq_counter,
            pair_counter=pair_counter,
            recent_numbers=recent_numbers,
            history_sets=history_sets,
        )

        scored_rows.append({
            "N1": int(row["N1"]),
            "N2": int(row["N2"]),
            "N3": int(row["N3"]),
            "N4": int(row["N4"]),
            "N5": int(row["N5"]),
            "Bonus": int(row["Bonus"]),
            "RegularSum": int(row["RegularSum"]),
            "HighCount": int(row["HighCount"]),
            "LowCount": int(row["LowCount"]),
            "OddCount": int(row["OddCount"]),
            "EvenCount": int(row["EvenCount"]),
            "ConsecutivePairs": int(
                row["ConsecutivePairs"]
            ),
            "EntropyScore": round(
                float(row["EntropyScore"]),
                4
            ),
            "GeneticFitnessScore": round(
                float(row["FitnessScore"]),
                4
            ),
            "EnsembleScore": round(
                ensemble_score,
                4
            ),
        })

    ensemble_df = pd.DataFrame(
        scored_rows
    )

    ensemble_df = ensemble_df.sort_values(
        by="EnsembleScore",
        ascending=False
    ).reset_index(drop=True)

    return ensemble_df


# =========================================================
# DIVERSITY FILTER
# =========================================================

def apply_diversity_filter(df):
    selected = []

    for _, row in df.iterrows():
        candidate_set = {
            int(row["N1"]),
            int(row["N2"]),
            int(row["N3"]),
            int(row["N4"]),
            int(row["N5"]),
        }

        ok = True

        for existing in selected:
            existing_set = {
                existing["N1"],
                existing["N2"],
                existing["N3"],
                existing["N4"],
                existing["N5"],
            }

            overlap = len(
                candidate_set.intersection(
                    existing_set
                )
            )

            if overlap > 3:
                ok = False
                break

        if ok:
            selected.append({
                "N1": int(row["N1"]),
                "N2": int(row["N2"]),
                "N3": int(row["N3"]),
                "N4": int(row["N4"]),
                "N5": int(row["N5"]),
                "Bonus": int(row["Bonus"]),
                "RegularSum": int(row["RegularSum"]),
                "HighCount": int(row["HighCount"]),
                "LowCount": int(row["LowCount"]),
                "OddCount": int(row["OddCount"]),
                "EvenCount": int(row["EvenCount"]),
                "ConsecutivePairs": int(
                    row["ConsecutivePairs"]
                ),
                "EntropyScore": float(
                    row["EntropyScore"]
                ),
                "GeneticFitnessScore": float(
                    row["GeneticFitnessScore"]
                ),
                "EnsembleScore": float(
                    row["EnsembleScore"]
                ),
            })

        if len(selected) >= FINAL_OUTPUT_ROWS:
            break

    return pd.DataFrame(selected)


# =========================================================
# EXPORT
# =========================================================

def export_ensemble_predictions():
    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    ensemble_df = build_ensemble_candidates()

    final_df = apply_diversity_filter(
        ensemble_df
    )

    final_df.insert(
        0,
        "PredictionRank",
        range(1, len(final_df) + 1)
    )

    final_df["ModelVersion"] = (
        "Ensemble_v1"
    )

    final_df["GeneratedAt"] = (
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:
        final_df.to_excel(
            writer,
            sheet_name="Final_Ensemble",
            index=False
        )

        ensemble_df.to_excel(
            writer,
            sheet_name="All_Candidates",
            index=False
        )

    print("\n======================================")
    print("ENSEMBLE EXPORT COMPLETE")
    print("======================================")
    print(f"Final Rows : {len(final_df)}")
    print(f"File       : {OUTPUT_FILE}")
    print("======================================\n")

    return final_df


# =========================================================
# CLI
# =========================================================

def main():
    export_ensemble_predictions()


if __name__ == "__main__":
    main()