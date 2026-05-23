from pathlib import Path

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
    / "uk49s_features.xlsx"
)

EXPORT_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "backtesting"
)

OUTPUT_FILE = (
    EXPORT_DIR
    / "uk49s_backtest_results.xlsx"
)


# =========================================================
# CONFIG
# =========================================================

TEST_DRAWS = 100
PREDICTIONS_PER_DRAW = 20

REGULAR_COLS = ["N1", "N2", "N3", "N4", "N5", "N6"]
BONUS_COL = "Bonus"

REGULAR_RANGE = range(1, 50)
BONUS_RANGE = range(1, 50)

RNG_SEED = 42
_rng = np.random.default_rng(RNG_SEED)


# =========================================================
# LOAD DATA
# =========================================================

def load_uk49s_features():
    if not FEATURES_FILE.exists():
        raise FileNotFoundError(
            f"UK49s features file not found:\n{FEATURES_FILE}\n\n"
            "Run this first:\n"
            "python -m src.lottery.features.uk49s_features"
        )

    df = pd.read_excel(
        FEATURES_FILE,
        sheet_name="UK49s_Features",
        engine="openpyxl"
    )

    df["DrawDate"] = pd.to_datetime(
        df["DrawDate"],
        errors="coerce"
    )

    for col in REGULAR_COLS + [BONUS_COL]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna(
        subset=["DrawDate"] + REGULAR_COLS + [BONUS_COL]
    )

    df = df.sort_values(
        by=["DrawDate", "DrawType"],
        ascending=[False, True]
    ).reset_index(drop=True)

    return df


# =========================================================
# HELPERS
# =========================================================

def get_regular_list(row):
    return [
        int(row["N1"]),
        int(row["N2"]),
        int(row["N3"]),
        int(row["N4"]),
        int(row["N5"]),
        int(row["N6"]),
    ]


def get_regular_set(row):
    return set(
        get_regular_list(row)
    )


def build_weighted_number_pool(train_df):
    regular_counts = {
        n: 1.0
        for n in REGULAR_RANGE
    }

    bonus_counts = {
        n: 1.0
        for n in BONUS_RANGE
    }

    for idx, row in train_df.iterrows():
        recency_weight = 0.985 ** idx

        for n in get_regular_list(row):
            regular_counts[n] += recency_weight

        bonus_counts[
            int(row["Bonus"])
        ] += recency_weight

    regular_total = sum(
        regular_counts.values()
    )

    bonus_total = sum(
        bonus_counts.values()
    )

    regular_probs = {
        n: regular_counts[n] / regular_total
        for n in regular_counts
    }

    bonus_probs = {
        n: bonus_counts[n] / bonus_total
        for n in bonus_counts
    }

    return regular_probs, bonus_probs


def weighted_sample_without_replacement(pool_probs, k):
    numbers = np.array(
        list(pool_probs.keys()),
        dtype=int
    )

    probs = np.array(
        list(pool_probs.values()),
        dtype=float
    )

    probs = probs / probs.sum()

    selected = _rng.choice(
        numbers,
        size=k,
        replace=False,
        p=probs
    )

    return sorted(
        selected.tolist()
    )


def generate_model_predictions(
    train_df,
    prediction_count=PREDICTIONS_PER_DRAW
):
    regular_probs, bonus_probs = build_weighted_number_pool(
        train_df
    )

    predictions = []
    seen = set()

    attempts = 0
    max_attempts = prediction_count * 200

    while (
        len(predictions) < prediction_count
        and attempts < max_attempts
    ):
        attempts += 1

        regulars = weighted_sample_without_replacement(
            regular_probs,
            k=6
        )

        bonus_pool = {
            n: bonus_probs[n]
            for n in BONUS_RANGE
            if n not in regulars
        }

        bonus = weighted_sample_without_replacement(
            bonus_pool,
            k=1
        )[0]

        regular_sum = sum(regulars)

        if regular_sum < 70 or regular_sum > 220:
            continue

        key = tuple(
            regulars + [bonus]
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
            "N6": regulars[5],
            "Bonus": bonus,
            "RegularSum": regular_sum,
        })

    return pd.DataFrame(predictions)


def generate_random_predictions(
    prediction_count=PREDICTIONS_PER_DRAW
):
    predictions = []
    seen = set()

    while len(predictions) < prediction_count:
        regulars = sorted(
            _rng.choice(
                np.arange(1, 50),
                size=6,
                replace=False
            ).tolist()
        )

        bonus_pool = [
            n for n in range(1, 50)
            if n not in regulars
        ]

        bonus = int(
            _rng.choice(
                bonus_pool,
                size=1
            )[0]
        )

        key = tuple(
            regulars + [bonus]
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
            "N6": regulars[5],
            "Bonus": bonus,
            "RegularSum": sum(regulars),
        })

    return pd.DataFrame(predictions)


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

    actual_bonus = int(
        actual_row["Bonus"]
    )

    rows = []

    for rank, pred in predictions_df.reset_index(drop=True).iterrows():
        predicted_regulars = {
            int(pred["N1"]),
            int(pred["N2"]),
            int(pred["N3"]),
            int(pred["N4"]),
            int(pred["N5"]),
            int(pred["N6"]),
        }

        regular_matches = len(
            predicted_regulars.intersection(
                actual_regulars
            )
        )

        bonus_match = (
            1
            if int(pred["Bonus"]) == actual_bonus
            else 0
        )

        total_score = (
            regular_matches
            + bonus_match
        )

        rows.append({
            "ModelName": model_name,
            "PredictionRank": rank + 1,
            "ActualDrawDate": actual_row["DrawDate"],
            "ActualDrawType": actual_row["DrawType"],
            "ActualNumbers": ",".join(
                map(str, sorted(actual_regulars))
            ),
            "ActualBonus": actual_bonus,
            "PredictedNumbers": ",".join(
                map(str, sorted(predicted_regulars))
            ),
            "PredictedBonus": int(pred["Bonus"]),
            "RegularMatches": regular_matches,
            "BonusMatch": bonus_match,
            "TotalScore": total_score,
        })

    return rows


# =========================================================
# BACKTEST ENGINE
# =========================================================

def run_uk49s_backtest(
    test_draws=TEST_DRAWS,
    predictions_per_draw=PREDICTIONS_PER_DRAW,
):
    df = load_uk49s_features()

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
    print("UK49s BACKTEST")
    print("======================================")
    print(f"Historical rows       : {len(df)}")
    print(f"Test draws            : {max_test_index}")
    print(f"Predictions per draw  : {predictions_per_draw}")
    print("======================================\n")

    for test_idx in range(max_test_index):
        actual_row = df.iloc[test_idx]

        train_df = df.iloc[
            test_idx + 1:
        ].copy()

        model_predictions = generate_model_predictions(
            train_df=train_df,
            prediction_count=predictions_per_draw
        )

        random_predictions = generate_random_predictions(
            prediction_count=predictions_per_draw
        )

        results.extend(
            score_predictions(
                predictions_df=model_predictions,
                actual_row=actual_row,
                model_name="UK49s_v1_weighted"
            )
        )

        results.extend(
            score_predictions(
                predictions_df=random_predictions,
                actual_row=actual_row,
                model_name="Random_Baseline"
            )
        )

        if (test_idx + 1) % 10 == 0:
            print(
                f"Completed {test_idx + 1} / {max_test_index} test draws..."
            )

    results_df = pd.DataFrame(results)

    return results_df


# =========================================================
# SUMMARIES
# =========================================================

def build_backtest_summary(results_df):
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

        bonus_hit_per_draw = draw_group[
            "BonusMatch"
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
            "DrawsWithBonusHit": int(
                (bonus_hit_per_draw >= 1).sum()
            ),
            "BonusHitDrawRate": round(
                (bonus_hit_per_draw >= 1).mean(),
                4
            ),
        })

    return pd.DataFrame(rows)


def build_rank_summary(results_df):
    summary = (
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
            BonusHitRate=("BonusMatch", "mean"),
        )
        .reset_index()
    )

    return summary


def build_draw_type_summary(results_df):
    summary = (
        results_df
        .groupby(
            [
                "ActualDrawType",
                "ModelName"
            ]
        )
        .agg(
            PredictionRows=("TotalScore", "count"),
            DrawsTested=("ActualDrawDate", "nunique"),
            AvgRegularMatches=("RegularMatches", "mean"),
            AvgTotalScore=("TotalScore", "mean"),
            MaxRegularMatches=("RegularMatches", "max"),
            MaxTotalScore=("TotalScore", "max"),
            BonusHitRate=("BonusMatch", "mean"),
        )
        .reset_index()
    )

    return summary


# =========================================================
# EXPORT
# =========================================================

def export_uk49s_backtest(
    test_draws=TEST_DRAWS,
    predictions_per_draw=PREDICTIONS_PER_DRAW,
):
    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results_df = run_uk49s_backtest(
        test_draws=test_draws,
        predictions_per_draw=predictions_per_draw,
    )

    summary_df = build_backtest_summary(
        results_df
    )

    rank_summary_df = build_rank_summary(
        results_df
    )

    draw_type_summary_df = build_draw_type_summary(
        results_df
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

        draw_type_summary_df.to_excel(
            writer,
            sheet_name="DrawType_Summary",
            index=False
        )

        results_df.to_excel(
            writer,
            sheet_name="Detailed_Results",
            index=False
        )

    print("\nUK49s backtest exported.")
    print(f"Rows: {len(results_df)}")
    print(f"File: {OUTPUT_FILE}")

    return results_df, summary_df


# =========================================================
# CLI
# =========================================================

def main():
    export_uk49s_backtest(
        test_draws=TEST_DRAWS,
        predictions_per_draw=PREDICTIONS_PER_DRAW,
    )


if __name__ == "__main__":
    main()