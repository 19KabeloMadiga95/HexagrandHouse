from pathlib import Path
from datetime import datetime
import itertools

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

BACKTEST_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "backtesting"
)

EXPORT_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "optimization"
)

OUTPUT_FILE = (
    EXPORT_DIR
    / "adaptive_weight_tuning_results.xlsx"
)


# =========================================================
# INPUT FILES
# =========================================================

GAME_BACKTEST_FILES = [
    {
        "GameFamily": "PowerBall",
        "File": BACKTEST_DIR / "powerball_model_comparison_backtest.xlsx",
    },
    {
        "GameFamily": "Lotto",
        "File": BACKTEST_DIR / "lotto_model_comparison_backtest.xlsx",
    },
    {
        "GameFamily": "Daily Lotto",
        "File": BACKTEST_DIR / "daily_lotto_model_comparison_backtest.xlsx",
    },
    {
        "GameFamily": "UK49s",
        "File": BACKTEST_DIR / "uk49s_model_comparison_backtest.xlsx",
    },
]


# =========================================================
# CONFIG SEARCH SPACE
# =========================================================

FREQUENCY_WEIGHTS = [
    1.0,
    1.5,
    2.0,
    2.5,
]

RECENCY_WEIGHTS = [
    1.0,
    1.5,
    2.0,
    2.5,
]

OVERDUE_WEIGHTS = [
    0.5,
    0.8,
    1.0,
]

PAIR_WEIGHTS = [
    0.2,
    0.4,
    0.6,
    0.8,
]

HYBRID_RANDOMNESS = [
    0.15,
    0.30,
    0.50,
]

HOT_CLUSTER_PENALTIES = [
    0.0,
    0.2,
    0.4,
    0.6,
]


# =========================================================
# HELPERS
# =========================================================

def safe_read_excel(
    path,
    sheet_name=0
):
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )

    except Exception:
        return pd.DataFrame()


def safe_numeric(
    df,
    col
):
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


def load_model_summaries():
    frames = []
    missing = []

    for item in GAME_BACKTEST_FILES:
        game_family = item["GameFamily"]
        path = item["File"]

        summary_df = safe_read_excel(
            path,
            "Summary"
        )

        if summary_df.empty:
            missing.append({
                "GameFamily": game_family,
                "File": str(path),
                "Status": "Missing or empty",
            })
            continue

        summary_df.insert(
            0,
            "GameFamily",
            game_family
        )

        frames.append(
            summary_df
        )

    if frames:
        combined = pd.concat(
            frames,
            ignore_index=True
        )

    else:
        combined = pd.DataFrame()

    return combined, pd.DataFrame(missing)


# =========================================================
# TUNING LOGIC
# =========================================================

def build_candidate_configs():
    rows = []

    config_id = 0

    for (
        frequency_weight,
        recency_weight,
        overdue_weight,
        pair_weight,
        hybrid_randomness,
        penalty_hot_cluster,
    ) in itertools.product(
        FREQUENCY_WEIGHTS,
        RECENCY_WEIGHTS,
        OVERDUE_WEIGHTS,
        PAIR_WEIGHTS,
        HYBRID_RANDOMNESS,
        HOT_CLUSTER_PENALTIES,
    ):
        config_id += 1

        rows.append({
            "ConfigID": config_id,
            "FrequencyWeight": frequency_weight,
            "RecencyWeight": recency_weight,
            "OverdueWeight": overdue_weight,
            "PairWeight": pair_weight,
            "HybridRandomness": hybrid_randomness,
            "PenaltyHotCluster": penalty_hot_cluster,
        })

    return pd.DataFrame(rows)


def infer_best_config_from_model_name(
    model_name
):
    model_name = str(
        model_name
    )

    if model_name == "Random_Baseline":
        return {
            "FrequencyWeight": 0.0,
            "RecencyWeight": 0.0,
            "OverdueWeight": 0.0,
            "PairWeight": 0.0,
            "HybridRandomness": 1.0,
            "PenaltyHotCluster": 0.0,
            "ModelType": "Random",
        }

    if "Weighted_AllHistory" in model_name:
        return {
            "FrequencyWeight": 2.5,
            "RecencyWeight": 1.5,
            "OverdueWeight": 1.0,
            "PairWeight": 0.8,
            "HybridRandomness": 0.0,
            "PenaltyHotCluster": 0.0,
            "ModelType": "Weighted_AllHistory",
        }

    if "Weighted_Recent" in model_name:
        return {
            "FrequencyWeight": 2.0,
            "RecencyWeight": 2.2,
            "OverdueWeight": 0.8,
            "PairWeight": 0.5,
            "HybridRandomness": 0.0,
            "PenaltyHotCluster": 0.0,
            "ModelType": "Weighted_Recent",
        }

    if "Hybrid_70Weighted_30Random" in model_name:
        return {
            "FrequencyWeight": 2.0,
            "RecencyWeight": 2.0,
            "OverdueWeight": 0.7,
            "PairWeight": 0.4,
            "HybridRandomness": 0.30,
            "PenaltyHotCluster": 0.2,
            "ModelType": "Hybrid_70_30",
        }

    if "Hybrid_50Weighted_50Random" in model_name:
        return {
            "FrequencyWeight": 1.5,
            "RecencyWeight": 1.5,
            "OverdueWeight": 0.5,
            "PairWeight": 0.2,
            "HybridRandomness": 0.50,
            "PenaltyHotCluster": 0.3,
            "ModelType": "Hybrid_50_50",
        }

    if "AntiCrowding" in model_name:
        return {
            "FrequencyWeight": 1.5,
            "RecencyWeight": 2.0,
            "OverdueWeight": 1.0,
            "PairWeight": 0.2,
            "HybridRandomness": 0.15,
            "PenaltyHotCluster": 0.6,
            "ModelType": "AntiCrowding",
        }

    return {
        "FrequencyWeight": None,
        "RecencyWeight": None,
        "OverdueWeight": None,
        "PairWeight": None,
        "HybridRandomness": None,
        "PenaltyHotCluster": None,
        "ModelType": "Unknown",
    }


def build_best_configurations(
    summary_df
):
    if summary_df.empty:
        return pd.DataFrame()

    df = summary_df.copy()

    numeric_cols = [
        "AverageBestRegularMatch_PerDraw",
        "DrawsWithAtLeast3RegularMatches",
        "AverageTotalScore_AllRows",
        "BonusHitDrawRate",
    ]

    for col in numeric_cols:
        df = safe_numeric(
            df,
            col
        )

    sort_cols = [
        col for col in [
            "AverageBestRegularMatch_PerDraw",
            "DrawsWithAtLeast3RegularMatches",
            "AverageTotalScore_AllRows",
            "BonusHitDrawRate",
        ]
        if col in df.columns
    ]

    df = df.sort_values(
        by=[
            "GameFamily"
        ] + sort_cols,
        ascending=[
            True
        ] + [
            False
        ] * len(sort_cols)
    )

    best_rows = (
        df
        .groupby("GameFamily")
        .head(1)
        .reset_index(drop=True)
    )

    config_rows = []

    for _, row in best_rows.iterrows():
        inferred = infer_best_config_from_model_name(
            row["ModelName"]
        )

        config_rows.append({
            "GameFamily": row["GameFamily"],
            "BestModelName": row["ModelName"],
            "AverageBestRegularMatch_PerDraw": row.get(
                "AverageBestRegularMatch_PerDraw",
                None
            ),
            "DrawsWithAtLeast3RegularMatches": row.get(
                "DrawsWithAtLeast3RegularMatches",
                None
            ),
            "AverageTotalScore_AllRows": row.get(
                "AverageTotalScore_AllRows",
                None
            ),
            "BonusHitDrawRate": row.get(
                "BonusHitDrawRate",
                None
            ),
            "RecommendedModelType": inferred["ModelType"],
            "FrequencyWeight": inferred["FrequencyWeight"],
            "RecencyWeight": inferred["RecencyWeight"],
            "OverdueWeight": inferred["OverdueWeight"],
            "PairWeight": inferred["PairWeight"],
            "HybridRandomness": inferred["HybridRandomness"],
            "PenaltyHotCluster": inferred["PenaltyHotCluster"],
            "GeneratedAt": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        })

    return pd.DataFrame(
        config_rows
    )


def build_model_rankings(
    summary_df
):
    if summary_df.empty:
        return pd.DataFrame()

    df = summary_df.copy()

    numeric_cols = [
        "AverageBestRegularMatch_PerDraw",
        "DrawsWithAtLeast3RegularMatches",
        "AverageTotalScore_AllRows",
        "BonusHitDrawRate",
    ]

    for col in numeric_cols:
        df = safe_numeric(
            df,
            col
        )

    df = df.sort_values(
        by=[
            "GameFamily",
            "AverageBestRegularMatch_PerDraw",
            "DrawsWithAtLeast3RegularMatches",
            "AverageTotalScore_AllRows",
        ],
        ascending=[
            True,
            False,
            False,
            False,
        ]
    ).reset_index(drop=True)

    df["GameRank"] = (
        df
        .groupby("GameFamily")
        .cumcount()
        + 1
    )

    return df


def build_tuner_notes():
    return pd.DataFrame([
        {
            "Section": "Purpose",
            "Note": "This tuner reads model comparison outputs and recommends the best existing configuration per game.",
        },
        {
            "Section": "Scope",
            "Note": "This is a Phase 1 compatibility tuner. It does not rerun expensive simulations.",
        },
        {
            "Section": "Reason",
            "Note": "The original adaptive tuner was too heavy for daily automation.",
        },
        {
            "Section": "Next Phase",
            "Note": "Phase 2 can add a true multi-game optimizer that dynamically reruns models across parameter grids.",
        },
    ])


# =========================================================
# EXPORT
# =========================================================

def run_adaptive_weight_tuner():
    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    summary_df, missing_df = load_model_summaries()

    candidate_configs_df = build_candidate_configs()

    model_rankings_df = build_model_rankings(
        summary_df
    )

    best_configurations_df = build_best_configurations(
        summary_df
    )

    tuner_notes_df = build_tuner_notes()

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        best_configurations_df.to_excel(
            writer,
            sheet_name="Best_Configurations",
            index=False
        )

        model_rankings_df.to_excel(
            writer,
            sheet_name="Model_Rankings",
            index=False
        )

        candidate_configs_df.to_excel(
            writer,
            sheet_name="Candidate_Configs",
            index=False
        )

        if not missing_df.empty:
            missing_df.to_excel(
                writer,
                sheet_name="Missing_Inputs",
                index=False
            )

        tuner_notes_df.to_excel(
            writer,
            sheet_name="Notes",
            index=False
        )

    print("\n======================================")
    print("ADAPTIVE WEIGHT TUNER COMPLETE")
    print("======================================")
    print("Mode: Phase 1 compatibility tuner")
    print(f"Best configs: {len(best_configurations_df)}")
    print(f"File        : {OUTPUT_FILE}")
    print("======================================\n")

    return best_configurations_df


# =========================================================
# CLI
# =========================================================

def main():
    run_adaptive_weight_tuner()


if __name__ == "__main__":
    main()