from pathlib import Path
from collections import Counter
from itertools import combinations

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
    / "backtesting"
)

OUTPUT_FILE = (
    EXPORT_DIR
    / "daily_lotto_model_comparison_backtest.xlsx"
)


# =========================================================
# CONFIG
# =========================================================

REGULAR_COLS = ["N1", "N2", "N3", "N4", "N5"]

REGULAR_RANGE = range(1, 37)

TEST_DRAWS = 100
PREDICTIONS_PER_DRAW = 10

RNG_SEED = 42
_rng = np.random.default_rng(RNG_SEED)


# =========================================================
# MODEL CONFIGS
# =========================================================

MODEL_CONFIGS = [
    {
        "ModelName": "Random_Baseline",
        "Mode": "random",
        "LookbackWindow": None,
        "FrequencyWeight": 0.0,
        "RecencyWeight": 0.0,
        "OverdueWeight": 0.0,
        "PairWeight": 0.0,
        "HybridRandomness": 1.0,
        "PenaltyHotCluster": 0.0,
    },
    {
        "ModelName": "Weighted_AllHistory_v1",
        "Mode": "weighted",
        "LookbackWindow": None,
        "FrequencyWeight": 2.5,
        "RecencyWeight": 1.5,
        "OverdueWeight": 1.0,
        "PairWeight": 0.8,
        "HybridRandomness": 0.0,
        "PenaltyHotCluster": 0.0,
    },
    {
        "ModelName": "Weighted_Recent100",
        "Mode": "weighted",
        "LookbackWindow": 100,
        "FrequencyWeight": 2.0,
        "RecencyWeight": 2.2,
        "OverdueWeight": 0.8,
        "PairWeight": 0.5,
        "HybridRandomness": 0.0,
        "PenaltyHotCluster": 0.0,
    },
    {
        "ModelName": "Hybrid_70Weighted_30Random",
        "Mode": "hybrid",
        "LookbackWindow": 100,
        "FrequencyWeight": 2.0,
        "RecencyWeight": 2.0,
        "OverdueWeight": 0.7,
        "PairWeight": 0.4,
        "HybridRandomness": 0.30,
        "PenaltyHotCluster": 0.2,
    },
    {
        "ModelName": "Hybrid_50Weighted_50Random",
        "Mode": "hybrid",
        "LookbackWindow": 100,
        "FrequencyWeight": 1.5,
        "RecencyWeight": 1.5,
        "OverdueWeight": 0.5,
        "PairWeight": 0.2,
        "HybridRandomness": 0.50,
        "PenaltyHotCluster": 0.3,
    },
    {
        "ModelName": "AntiCrowding_Recent100",
        "Mode": "weighted",
        "LookbackWindow": 100,
        "FrequencyWeight": 1.5,
        "RecencyWeight": 2.0,
        "OverdueWeight": 1.0,
        "PairWeight": 0.2,
        "HybridRandomness": 0.15,
        "PenaltyHotCluster": 0.6,
    },
]


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

    df["DrawDate"] = pd.to_datetime(
        df["DrawDate"],
        errors="coerce"
    )

    for col in REGULAR_COLS:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna(
        subset=["DrawDate"] + REGULAR_COLS
    )

    df = df.sort_values(
        by="DrawDate",
        ascending=False
    ).reset_index(drop=True)

    return df


# =========================================================
# HELPERS
# =========================================================

def normalise_01(series):
    series = pd.Series(
        series,
        dtype=float
    )

    lo = series.min()
    hi = series.max()

    if hi <= lo:
        return pd.Series(
            0.5,
            index=series.index
        )

    return (series - lo) / (hi - lo)


def get_regular_list(row):
    return [
        int(row["N1"]),
        int(row["N2"]),
        int(row["N3"]),
        int(row["N4"]),
        int(row["N5"]),
    ]


def get_regular_set(row):
    return set(
        get_regular_list(row)
    )


def count_consecutive(numbers):
    numbers = sorted(numbers)

    count = 0

    for i in range(len(numbers) - 1):
        if numbers[i + 1] - numbers[i] == 1:
            count += 1

    return count


def count_high_low(numbers):
    low = sum(
        1 for n in numbers
        if n <= 18
    )

    high = len(numbers) - low

    return high, low


def count_odd_even(numbers):
    odd = sum(
        1 for n in numbers
        if n % 2 != 0
    )

    even = len(numbers) - odd

    return odd, even


def weighted_choice_no_replace(
    pool,
    weights,
    k
):
    pool = np.array(
        pool,
        dtype=int
    )

    weights = np.array(
        weights,
        dtype=float
    )

    if weights.sum() <= 0:
        probs = np.ones(
            len(pool)
        ) / len(pool)

    else:
        probs = weights / weights.sum()

    return sorted(
        _rng.choice(
            pool,
            size=k,
            replace=False,
            p=probs
        ).tolist()
    )


# =========================================================
# LEARNING LOGIC
# =========================================================

def apply_lookback(
    train_df,
    lookback_window
):
    if lookback_window is None:
        return train_df.copy()

    return train_df.head(
        lookback_window
    ).copy()


def build_frequency_scores(train_df):
    reg_counter = Counter()

    for _, row in train_df.iterrows():
        for n in get_regular_list(row):
            reg_counter[n] += 1

    reg_scores = pd.Series({
        n: reg_counter[n]
        for n in REGULAR_RANGE
    })

    return normalise_01(
        reg_scores
    )


def build_recency_scores(
    train_df,
    decay=0.975
):
    reg_scores = pd.Series(
        0.0,
        index=pd.Index(REGULAR_RANGE),
        dtype=float
    )

    for idx, row in train_df.iterrows():
        weight = decay ** idx

        for n in get_regular_list(row):
            reg_scores.loc[n] += weight

    return normalise_01(
        reg_scores
    )


def build_overdue_scores(train_df):
    last_seen = {
        n: None
        for n in REGULAR_RANGE
    }

    for idx, row in train_df.iterrows():
        for n in get_regular_list(row):
            if last_seen[n] is None:
                last_seen[n] = idx

    scores = {}

    for n in REGULAR_RANGE:
        scores[n] = (
            len(train_df)
            if last_seen[n] is None
            else last_seen[n]
        )

    return normalise_01(
        pd.Series(scores)
    )


def build_pair_scores(train_df):
    pair_counter = Counter()

    for _, row in train_df.iterrows():
        numbers = sorted(
            get_regular_list(row)
        )

        for pair in combinations(
            numbers,
            2
        ):
            pair_counter[pair] += 1

    return pair_counter


def build_number_weights(
    train_df,
    config
):
    freq_reg = build_frequency_scores(
        train_df
    )

    rec_reg = build_recency_scores(
        train_df
    )

    overdue_reg = build_overdue_scores(
        train_df
    )

    reg_weights = (
        config["FrequencyWeight"] * freq_reg
        + config["RecencyWeight"] * rec_reg
        + config["OverdueWeight"] * overdue_reg
    )

    reg_weights = reg_weights.clip(
        lower=0.001
    )

    return reg_weights.to_dict()


def build_hot_numbers(
    train_df,
    top_n=10
):
    counter = Counter()

    for _, row in train_df.iterrows():
        for n in get_regular_list(row):
            counter[n] += 1

    return set([
        n for n, _ in counter.most_common(top_n)
    ])


# =========================================================
# SCORING / FILTERS
# =========================================================

def score_pair_strength(
    numbers,
    pair_counter
):
    score = 0

    for pair in combinations(
        sorted(numbers),
        2
    ):
        score += pair_counter[pair]

    return score


def score_pattern(numbers):
    high, low = count_high_low(numbers)
    odd, even = count_odd_even(numbers)

    total = sum(numbers)
    consecutive = count_consecutive(numbers)

    score = 0

    if (high, low) in [(2, 3), (3, 2)]:
        score += 4

    elif (high, low) in [(1, 4), (4, 1)]:
        score += 1

    if (odd, even) in [(2, 3), (3, 2)]:
        score += 4

    elif (odd, even) in [(1, 4), (4, 1)]:
        score += 1

    if 70 <= total <= 110:
        score += 4

    elif 45 <= total <= 145:
        score += 2

    if consecutive <= 1:
        score += 3

    elif consecutive == 2:
        score += 1

    return score


def hot_cluster_penalty(
    numbers,
    hot_numbers
):
    return sum(
        1 for n in numbers
        if n in hot_numbers
    )


def passes_basic_filters(numbers):
    total = sum(numbers)

    if total < 45 or total > 145:
        return False

    if count_consecutive(numbers) > 3:
        return False

    return True


# =========================================================
# PREDICTION GENERATORS
# =========================================================

def generate_random_predictions(prediction_count):
    predictions = []
    seen = set()

    while len(predictions) < prediction_count:
        regulars = sorted(
            _rng.choice(
                np.arange(1, 37),
                size=5,
                replace=False
            ).tolist()
        )

        key = tuple(
            regulars
        )

        if key in seen:
            continue

        seen.add(key)

        predictions.append({
            "N1": regulars[0],
            "N2": regulars[1],
            "N3": regulars[2],
            "N4": regulars[3],
            "N5": regulars[4],
            "RegularSum": sum(regulars),
            "ModelRawScore": 0,
        })

    return pd.DataFrame(predictions)


def generate_weighted_predictions(
    train_df,
    config,
    prediction_count
):
    model_train_df = apply_lookback(
        train_df,
        config["LookbackWindow"]
    )

    reg_weights = build_number_weights(
        model_train_df,
        config
    )

    pair_counter = build_pair_scores(
        model_train_df
    )

    hot_numbers = build_hot_numbers(
        model_train_df,
        top_n=10
    )

    candidates = []
    seen = set()

    attempts = 0
    max_attempts = prediction_count * 600

    while (
        len(candidates) < prediction_count * 50
        and attempts < max_attempts
    ):
        attempts += 1

        hybrid_randomness = config[
            "HybridRandomness"
        ]

        if (
            config["Mode"] == "hybrid"
            and _rng.random() < hybrid_randomness
        ):
            regulars = sorted(
                _rng.choice(
                    np.arange(1, 37),
                    size=5,
                    replace=False
                ).tolist()
            )

        else:
            regulars = weighted_choice_no_replace(
                pool=list(REGULAR_RANGE),
                weights=[
                    reg_weights[n]
                    for n in REGULAR_RANGE
                ],
                k=5
            )

        key = tuple(
            regulars
        )

        if key in seen:
            continue

        if not passes_basic_filters(
            regulars
        ):
            continue

        seen.add(key)

        base_score = sum(
            reg_weights[n]
            for n in regulars
        )

        pair_score = score_pair_strength(
            regulars,
            pair_counter
        )

        pattern_score = score_pattern(
            regulars
        )

        penalty = hot_cluster_penalty(
            regulars,
            hot_numbers
        )

        raw_score = (
            base_score
            + config["PairWeight"] * pair_score
            + pattern_score
            - config["PenaltyHotCluster"] * penalty
        )

        candidates.append({
            "N1": regulars[0],
            "N2": regulars[1],
            "N3": regulars[2],
            "N4": regulars[3],
            "N5": regulars[4],
            "RegularSum": sum(regulars),
            "ModelRawScore": raw_score,
        })

    if not candidates:
        return generate_random_predictions(
            prediction_count
        )

    candidates_df = pd.DataFrame(
        candidates
    )

    candidates_df = candidates_df.sort_values(
        by="ModelRawScore",
        ascending=False
    ).reset_index(drop=True)

    selected = []

    for _, row in candidates_df.iterrows():
        candidate = [
            int(row["N1"]),
            int(row["N2"]),
            int(row["N3"]),
            int(row["N4"]),
            int(row["N5"]),
        ]

        candidate_set = set(
            candidate
        )

        ok = True

        for existing in selected:
            existing_set = set(
                existing
            )

            if len(
                candidate_set.intersection(
                    existing_set
                )
            ) > 3:
                ok = False
                break

        if ok:
            selected.append(
                candidate
            )

        if len(selected) >= prediction_count:
            break

    final_rows = []

    for candidate in selected:
        final_rows.append({
            "N1": candidate[0],
            "N2": candidate[1],
            "N3": candidate[2],
            "N4": candidate[3],
            "N5": candidate[4],
            "RegularSum": sum(candidate),
            "ModelRawScore": 0,
        })

    return pd.DataFrame(final_rows)


def generate_predictions_for_model(
    train_df,
    config,
    prediction_count
):
    if config["Mode"] == "random":
        return generate_random_predictions(
            prediction_count
        )

    return generate_weighted_predictions(
        train_df=train_df,
        config=config,
        prediction_count=prediction_count
    )


# =========================================================
# SCORING
# =========================================================

def score_predictions(
    predictions_df,
    actual_row,
    model_name
):
    actual_regulars = get_regular_set(
        actual_row
    )

    rows = []

    for rank, pred in predictions_df.reset_index(drop=True).iterrows():
        predicted_regulars = {
            int(pred["N1"]),
            int(pred["N2"]),
            int(pred["N3"]),
            int(pred["N4"]),
            int(pred["N5"]),
        }

        regular_matches = len(
            predicted_regulars.intersection(
                actual_regulars
            )
        )

        total_score = regular_matches

        rows.append({
            "ModelName": model_name,
            "PredictionRank": rank + 1,
            "ActualDrawDate": actual_row["DrawDate"],
            "ActualNumbers": ",".join(
                map(str, sorted(actual_regulars))
            ),
            "PredictedNumbers": ",".join(
                map(str, sorted(predicted_regulars))
            ),
            "RegularMatches": regular_matches,
            "TotalScore": total_score,
        })

    return rows


# =========================================================
# BACKTEST ENGINE
# =========================================================

def run_daily_lotto_model_comparison_backtest(
    test_draws=TEST_DRAWS,
    predictions_per_draw=PREDICTIONS_PER_DRAW,
):
    df = load_daily_lotto_features()

    if len(df) <= test_draws + 20:
        raise ValueError(
            f"Not enough rows to backtest. Rows available: {len(df)}"
        )

    results = []

    max_test_index = min(
        test_draws,
        len(df) - 20
    )

    print("\n======================================")
    print("DAILY LOTTO MODEL COMPARISON BACKTEST")
    print("======================================")
    print(f"Historical rows       : {len(df)}")
    print(f"Test draws            : {max_test_index}")
    print(f"Predictions per draw  : {predictions_per_draw}")
    print(f"Models tested         : {len(MODEL_CONFIGS)}")
    print("======================================\n")

    for test_idx in range(
        max_test_index
    ):
        actual_row = df.iloc[
            test_idx
        ]

        train_df = df.iloc[
            test_idx + 1:
        ].copy()

        for config in MODEL_CONFIGS:
            predictions = generate_predictions_for_model(
                train_df=train_df,
                config=config,
                prediction_count=predictions_per_draw
            )

            results.extend(
                score_predictions(
                    predictions_df=predictions,
                    actual_row=actual_row,
                    model_name=config["ModelName"]
                )
            )

        if (test_idx + 1) % 10 == 0:
            print(
                f"Completed {test_idx + 1} / {max_test_index} test draws..."
            )

    results_df = pd.DataFrame(
        results
    )

    return results_df


# =========================================================
# SUMMARIES
# =========================================================

def build_model_summary(results_df):
    rows = []

    grouped = results_df.groupby(
        "ModelName"
    )

    for model_name, group in grouped:
        draw_group = group.groupby(
            "ActualDrawDate"
        )

        best_per_draw = draw_group[
            "TotalScore"
        ].max()

        best_regular_per_draw = draw_group[
            "RegularMatches"
        ].max()

        rows.append({
            "ModelName": model_name,
            "PredictionRows": len(group),
            "DrawsTested": group["ActualDrawDate"].nunique(),
            "AverageRegularMatches_AllRows": round(
                group["RegularMatches"].mean(),
                4
            ),
            "AverageTotalScore_AllRows": round(
                group["TotalScore"].mean(),
                4
            ),
            "BestRegularMatch_AnyRow": int(
                group["RegularMatches"].max()
            ),
            "BestTotalScore_AnyRow": int(
                group["TotalScore"].max()
            ),
            "AverageBestScore_PerDraw": round(
                best_per_draw.mean(),
                4
            ),
            "AverageBestRegularMatch_PerDraw": round(
                best_regular_per_draw.mean(),
                4
            ),
            "DrawsWithAtLeast2RegularMatches": int(
                (best_regular_per_draw >= 2).sum()
            ),
            "DrawsWithAtLeast3RegularMatches": int(
                (best_regular_per_draw >= 3).sum()
            ),
        })

    summary = pd.DataFrame(
        rows
    )

    summary = summary.sort_values(
        by=[
            "AverageBestRegularMatch_PerDraw",
            "DrawsWithAtLeast3RegularMatches",
            "AverageTotalScore_AllRows",
        ],
        ascending=[
            False,
            False,
            False,
        ]
    ).reset_index(drop=True)

    summary["Rank"] = summary.index + 1

    return summary


def build_rank_summary(results_df):
    return (
        results_df
        .groupby(
            [
                "ModelName",
                "PredictionRank"
            ]
        )
        .agg(
            PredictionRows=("TotalScore", "count"),
            AvgRegularMatches=("RegularMatches", "mean"),
            AvgTotalScore=("TotalScore", "mean"),
            MaxRegularMatches=("RegularMatches", "max"),
            MaxTotalScore=("TotalScore", "max"),
        )
        .reset_index()
    )


def build_hit_distribution(results_df):
    return (
        results_df
        .groupby(
            [
                "ModelName",
                "RegularMatches"
            ]
        )
        .agg(
            Count=("RegularMatches", "count")
        )
        .reset_index()
    )


# =========================================================
# EXPORT
# =========================================================

def export_daily_lotto_model_comparison_backtest(
    test_draws=TEST_DRAWS,
    predictions_per_draw=PREDICTIONS_PER_DRAW,
):
    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results_df = run_daily_lotto_model_comparison_backtest(
        test_draws=test_draws,
        predictions_per_draw=predictions_per_draw,
    )

    summary_df = build_model_summary(
        results_df
    )

    rank_summary_df = build_rank_summary(
        results_df
    )

    hit_distribution_df = build_hit_distribution(
        results_df
    )

    config_df = pd.DataFrame(
        MODEL_CONFIGS
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        rank_summary_df.to_excel(
            writer,
            sheet_name="Rank_Summary",
            index=False
        )

        hit_distribution_df.to_excel(
            writer,
            sheet_name="Hit_Distribution",
            index=False
        )

        config_df.to_excel(
            writer,
            sheet_name="Model_Configs",
            index=False
        )

        results_df.to_excel(
            writer,
            sheet_name="Detailed_Results",
            index=False
        )

    print("\nDaily Lotto model comparison backtest exported.")
    print(f"Rows: {len(results_df)}")
    print(f"File: {OUTPUT_FILE}")

    return results_df, summary_df


# =========================================================
# CLI
# =========================================================

def main():
    export_daily_lotto_model_comparison_backtest(
        test_draws=TEST_DRAWS,
        predictions_per_draw=PREDICTIONS_PER_DRAW,
    )


if __name__ == "__main__":
    main()